<?php

declare(strict_types=1);

namespace Nawras\License;

use Nawras\Db\Connection;

/**
 * Reads the ledger. All license evidence flows through here — nothing queries
 * game_licenses directly from controllers/CLI, so the auditor's input shape has
 * exactly one owner.
 */
final class LicenseRepository
{
    public function __construct(private readonly Connection $db)
    {
    }

    /**
     * Every game with its license rows (empty list when none) — the auditor's input.
     *
     * @return list<array<string, mixed>>
     */
    public function scanAll(): array
    {
        $rows = $this->db->all(
            'SELECT g.id AS game_id, g.slug, g.status, g.kind, g.local_path,
                    l.provider, l.external_id, l.license_type, l.license_ref,
                    l.upstream_repo, l.commit_sha, l.license_path, l.license_sha256,
                    l.proof_url, l.invoice_ref, l.allow_origins,
                    l.attribution_required, l.attribution_html,
                    l.status AS license_status, l.expires_at
             FROM games g
             LEFT JOIN game_licenses l ON l.game_id = g.id
             ORDER BY g.id'
        );

        return $this->groupByGame($rows);
    }

    /** @return array<string, mixed>|null */
    public function scanGame(string $slug): ?array
    {
        $rows = $this->db->all(
            'SELECT g.id AS game_id, g.slug, g.status, g.kind, g.local_path,
                    l.provider, l.external_id, l.license_type, l.license_ref,
                    l.upstream_repo, l.commit_sha, l.license_path, l.license_sha256,
                    l.proof_url, l.invoice_ref, l.allow_origins,
                    l.attribution_required, l.attribution_html,
                    l.status AS license_status, l.expires_at
             FROM games g
             LEFT JOIN game_licenses l ON l.game_id = g.id
             WHERE g.slug = ?',
            [$slug]
        );
        $games = $this->groupByGame($rows);

        return $games[0] ?? null;
    }

    /** Regroups the LEFT JOIN flat rows into per-game records. */
    private function groupByGame(array $rows): array
    {
        $games = [];
        foreach ($rows as $row) {
            $id = (int) $row['game_id'];
            if (!isset($games[$id])) {
                $games[$id] = [
                    'game_id' => $id,
                    'slug' => (string) $row['slug'],
                    'status' => (string) $row['status'],
                    'kind' => (string) $row['kind'],
                    'local_path' => (string) $row['local_path'],
                    'licenses' => [],
                ];
            }
            if ($row['provider'] !== null) {
                $games[$id]['licenses'][] = $row;
            }
        }

        return \array_values($games);
    }
}
