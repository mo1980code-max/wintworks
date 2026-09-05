<?php

declare(strict_types=1);

namespace Nawras\License;

/**
 * The pure license auditor — the product's "no infringement" engine.
 *
 * Takes ledger rows (game info + zero or more license rows each) and returns violations.
 * No I/O here: the repository assembles rows, the CLI/static exporter feeds them in.
 * The SAME shared rules are enforced by tools/audit_ledger.py on the static side;
 * tools/check_audit_parity.py fails the build if the two engines drift.
 *
 * Severity: an ERROR hides the game from visitors and fails `licenses:audit`;
 * a WARNING fails only under --strict (used by release gating).
 */
final class LicenseAuditor
{
    /** SPDX refs this product may ship, plus the two non-SPDX kinds. MUST match tools/audit_ledger.py. */
    public const ALLOWED_REFS = [
        'MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC', '0BSD',
        'Unlicense', 'Zlib', 'OFL-1.1', 'CC0-1.0', 'publisher-agreement', 'own-licence',
    ];

    /** Anything matching these prefixes is banned from the paid package. MUST match tools/audit_ledger.py. */
    public const FORBIDDEN_PREFIXES = ['GPL', 'AGPL', 'LGPL', 'CC-BY-NC', 'BSD-4', 'NPOSL', 'SSPL'];

    public const LICENSE_TYPES = ['oss', 'publisher-agreement', 'own'];

    /**
     * Shared rule names (enforced identically by the Python twin).
     * MUST stay byte-identical to SHARED_RULES in tools/audit_ledger.py.
     */
    public const SHARED_RULES = [
        'slug', 'no_license_row', 'license_type', 'license_status', 'license_expiry',
        'copyleft', 'allow_list', 'proof_upstream', 'pin', 'external_id',
        'runtime', 'attribution',
    ];

    /** Rules that need a filesystem or DB — PHP engine only. */
    public const PHP_ONLY_RULES = ['license_drift', 'invoice', 'local_path', 'provider_gate'];

    /**
     * @param array{providers?: list<string>, strict?: bool, now?: string} $config
     */
    public function __construct(private readonly array $config = [])
    {
    }

    /**
     * Audits one game. $row carries game fields + `licenses` = list of license rows.
     *
     * @return array{errors: list<array{rule: string, slug: string, message: string}>, warnings: list<array{rule: string, slug: string, message: string}>}
     */
    public function scanGame(array $game): array
    {
        $errors = [];
        $warnings = [];
        $slug = (string) ($game['slug'] ?? '');

        // rule: slug — a ledger entry without a usable slug can never be enforced
        if ($slug === '' || !\preg_match('/^[a-z0-9][a-z0-9-]{1,78}[a-z0-9]$/', $slug)) {
            $errors[] = self::violation('slug', $slug !== '' ? $slug : '(empty)', 'game slug missing or malformed');
        }

        // rule: no_license_row — a published game without any license evidence
        $licenses = \array_values((array) ($game['licenses'] ?? []));
        if ($licenses === [] && (string) ($game['status'] ?? '') === 'published') {
            $errors[] = self::violation('no_license_row', $slug, 'published game has no license row — hidden from visitors');
        }

        foreach ($licenses as $license) {
            [$e, $w] = $this->scanLicense($slug, $game, $license);
            $errors = \array_merge($errors, $e);
            $warnings = \array_merge($warnings, $w);
        }

        return ['errors' => $errors, 'warnings' => $warnings];
    }

    /** @return array{0: list<array>, 1: list<array>} */
    private function scanLicense(string $slug, array $game, array $license): array
    {
        $errors = [];
        $warnings = [];
        $type = (string) ($license['license_type'] ?? '');
        $ref = (string) ($license['license_ref'] ?? '');
        $status = (string) ($license['license_status'] ?? '');
        $provider = (string) ($license['provider'] ?? 'own');
        $externalId = (string) ($license['external_id'] ?? '');
        $sha = (string) ($license['commit_sha'] ?? '');
        $now = (string) ($this->config['now'] ?? \gmdate('Y-m-d'));

        // rule: license_type
        if (!\in_array($type, self::LICENSE_TYPES, true)) {
            $errors[] = self::violation('license_type', $slug, "license type '{$type}' is not one of: " . \implode(', ', self::LICENSE_TYPES));
        }

        // rule: license_status — withdrawn/superseded rows may not back a live game
        if ($status !== 'active') {
            $errors[] = self::violation('license_status', $slug, "license status '{$status}' is not active");
        }

        // rules: copyleft + allow_list — the hard IP wall
        foreach (self::FORBIDDEN_PREFIXES as $prefix) {
            if ($ref !== '' && \strncasecmp($ref, $prefix, \strlen($prefix)) === 0) {
                $errors[] = self::violation('copyleft', $slug, "'{$ref}' is copyleft/non-commercial — banned from this product");
                break;
            }
        }
        if (!\in_array($ref, self::ALLOWED_REFS, true)) {
            $errors[] = self::violation('allow_list', $slug, "license ref '{$ref}' is not in the allow-list");
        }

        if ($type === 'oss') {
            // rule: proof_upstream — an OSS row must point at its source
            $repo = (string) ($license['upstream_repo'] ?? '');
            $proof = (string) ($license['proof_url'] ?? '');
            if ($repo === '' || $proof === '') {
                $errors[] = self::violation('proof_upstream', $slug, 'oss license needs upstream_repo and proof_url');
            }

            // rule: pin — must be pinned to a full 40-hex commit
            if (!\preg_match('/^[0-9a-f]{40}$/', $sha)) {
                $errors[] = self::violation('pin', $slug, "commit pin '" . \substr($sha, 0, 12) . "…' is not a full 40-hex sha");
            }

            // rule: license_expiry — expired third-party licenses cannot be re-proven silently
            $expires = (string) ($license['expires_at'] ?? '');
            if ($expires !== '' && $expires < $now) {
                $errors[] = self::violation('license_expiry', $slug, "license expired {$expires}");
            }
        }

        // rule: external_id — feed identity shape (also our SSRF/SQL hygiene boundary)
        if ($provider !== 'own' && !\preg_match('/^[A-Za-z0-9_-]{4,64}$/', $externalId)) {
            $errors[] = self::violation('external_id', $slug, "external_id '{$externalId}' must match ^[A-Za-z0-9_-]{4,64}$");
        }

        // rule: runtime — internal consistency a file check cannot fix later
        if ($type === 'own' && \trim((string) ($license['local_path'] ?? ($game['local_path'] ?? ''))) === '') {
            $errors[] = self::violation('runtime', $slug, 'own game has no local_path — nothing lawful to serve');
        }
        if ($type === 'publisher-agreement' && \trim((string) ($license['allow_origins'] ?? '')) === '') {
            $errors[] = self::violation('runtime', $slug, 'publisher-agreement rows must record allow_origins (the embed hosts the contract covers)');
        }

        // rule: attribution — copyleft-free licenses may still demand visible credit
        if (!empty($license['attribution_required']) && \trim((string) ($license['attribution_html'] ?? '')) === '') {
            $warnings[] = self::violation('attribution', $slug, 'attribution_required is set but attribution_html is empty');
        }

        // PHP-only rules (need a filesystem / provider config)
        $drift = $this->ruleLicenseDrift($slug, $license);
        if ($drift !== null) {
            $errors[] = $drift;
        }
        if ($type === 'publisher-agreement' && \trim((string) ($license['invoice_ref'] ?? '')) === '') {
            $errors[] = self::violation('invoice', $slug, 'publisher-agreement needs the paid invoice_ref');
        }
        if ($type === 'own' && \trim((string) ($game['local_path'] ?? '')) !== '' && !\is_dir((string) $game['local_path'])) {
            $errors[] = self::violation('local_path', $slug, 'own game local_path does not exist on disk');
        }
        $providers = (array) ($this->config['providers'] ?? []);
        if ($providers !== [] && !\in_array($provider, $providers, true)) {
            $errors[] = self::violation('provider_gate', $slug, "provider '{$provider}' is not enabled in config");
        }

        return [$errors, $warnings];
    }

    /** rule: license_drift — stored hash of the license FILE must match the file on disk. */
    private function ruleLicenseDrift(string $slug, array $license): ?array
    {
        $path = (string) ($license['license_path'] ?? '');
        $stored = (string) ($license['license_sha256'] ?? '');
        if ($path === '' || $stored === '') {
            return null; // nothing pinned yet: proof_upstream covers the oss case
        }
        if (!\is_file($path)) {
            return self::violation('license_drift', $slug, "license file missing: {$path}");
        }
        $actual = \hash_file('sha256', $path);
        if ($actual !== null && !\hash_equals($stored, $actual)) {
            return self::violation('license_drift', $slug, "license text changed upstream ({$path}) — re-capture before shipping");
        }

        return null;
    }

    /** Audits many games; returns the aggregate report. */
    public function scanAll(array $games): array
    {
        $errors = [];
        $warnings = [];
        foreach ($games as $game) {
            $result = $this->scanGame($game);
            $errors = \array_merge($errors, $result['errors']);
            $warnings = \array_merge($warnings, $result['warnings']);
        }

        return ['errors' => $errors, 'warnings' => $warnings, 'games' => \count($games)];
    }

    /** Game ids with zero errors (warnings allowed unless strict) — the visibility boundary. */
    public function cleanGameIds(array $games, bool $strict = false): array
    {
        $out = [];
        foreach ($games as $game) {
            $result = $this->scanGame($game);
            if ($result['errors'] === [] && (!$strict || $result['warnings'] === [])) {
                $out[] = (int) ($game['game_id'] ?? $game['id'] ?? 0);
            }
        }

        return $out;
    }

    private static function violation(string $rule, string $slug, string $message): array
    {
        return ['rule' => $rule, 'slug' => $slug, 'message' => $message];
    }
}
