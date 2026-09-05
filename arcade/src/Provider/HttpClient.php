<?php

declare(strict_types=1);

namespace Nawras\Provider;

use Nawras\Db\Connection;

/**
 * SSRF-hardened HTTP client — the ONLY door from this codebase to the outside network.
 *
 * Threat model (marketplace scripts die by this): a buyer enters a provider URL, a feed
 * returns a "thumbnail" pointing at http://169.254.169.254/latest/meta-data or the
 * buyer's own localhost admin panel — and a naive file_get_contents() hands the attacker
 * the keys. Here every hop is re-validated: allow-list of HOSTS, private/loopback/link-
 * range IP literals rejected by shape, plain http refused (installed buyers may run
 * without TLS outbound, so a config flag can relax it consciously, never by accident),
 * redirect chains re-checked hop by hop, and the body size capped mid-stream.
 *
 * Every run lands in provider_runs / provider_games — the ledger discipline extends to
 * the network layer: what was fetched, from where, and whether it became a game.
 */
final class HttpClient
{
    private const MAX_REDIRECTS = 3;

    /** IP-literal prefixes we never talk to, no matter what the DNS says. */
    private const BLOCKED_IP_PREFIXES = [
        '0.', '10.', '127.', '169.254.', '192.0.0.', '192.168.',
        '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
        '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.',
        '100.64.', '100.65.', '100.66.', '100.67.', '100.68.', '100.69.', '100.70.', '100.71.',
        '100.72.', '100.73.', '100.74.', '100.75.', '100.76.', '100.77.', '100.78.', '100.79.',
        '100.80.', '100.81.', '100.82.', '100.83.', '100.84.', '100.85.', '100.86.', '100.87.',
        '100.88.', '100.89.', '100.90.', '100.91.', '100.92.', '100.93.', '100.94.', '100.95.',
        '100.96.', '100.97.', '100.98.', '100.99.', '100.100.', '100.101.', '100.102.', '100.103.',
        '100.104.', '100.105.', '100.106.', '100.107.', '100.108.', '100.109.', '100.110.', '100.111.',
        '100.112.', '100.113.', '100.114.', '100.115.', '100.116.', '100.117.', '100.118.', '100.119.',
        '100.120.', '100.121.', '100.122.', '100.123.', '100.124.', '100.125.', '100.126.', '100.127.',
        '198.18.', '198.19.',
    ];

    public function __construct(
        private readonly Connection $db,
        private readonly array $allowHosts,
        private readonly int $timeoutSeconds = 10,
        private readonly int $maxBytes = 2_000_000,
        private readonly bool $allowHttp = false,
    ) {
    }

    /**
     * GET a URL. Returns ['ok'=>bool,'status'=>int,'body'=>string,'error'=>string].
     * Never throws for network conditions — callers decide, the ledger remembers.
     */
    public function get(string $url, string $purpose = ''): array
    {
        $runId = $this->beginRun($url, $purpose);
        $result = $this->fetchWithRedirects($url);
        $this->finishRun($runId, $result['ok'] ? 'ok' : 'error', $result['error'] ?: (string) $result['status']);

        return $result;
    }

    /** @return array{ok: bool, status: int, body: string, error: string} */
    private function fetchWithRedirects(string $url): array
    {
        $hops = 0;
        while (true) {
            $guard = $this->guard($url);
            if ($guard !== null) {
                return ['ok' => false, 'status' => 0, 'body' => '', 'error' => $guard];
            }
            if ($hops >= self::MAX_REDIRECTS) {
                return ['ok' => false, 'status' => 0, 'body' => '', 'error' => 'too many redirects'];
            }

            $step = $this->singleGet($url);
            if ($step['kind'] === 'final') {
                return $step['result'];
            }
            $url = (string) $step['location'];
            $hops++;
        }
    }

    /** @return array{kind:'final', result: array}|array{kind:'redirect', location:string} */
    private function singleGet(string $url): array
    {
        $ch = \curl_init($url);
        $body = '';
        \curl_setopt_array($ch, [
            \CURLOPT_RETURNTRANSFER => false,
            \CURLOPT_FOLLOWLOCATION => false,
            \CURLOPT_CONNECTTIMEOUT => $this->timeoutSeconds,
            \CURLOPT_TIMEOUT => $this->timeoutSeconds,
            \CURLOPT_USERAGENT => 'NawrasArcade/0.3 (+provider sync; ledger-audited)',
            \CURLOPT_WRITEFUNCTION => function ($ch, string $chunk) use (&$body): int {
                $body .= $chunk;
                if (\strlen($body) > $this->maxBytes) {
                    return -1; // abort mid-stream: body cap is not negotiable
                }

                return \strlen($chunk);
            },
        ]);
        \curl_exec($ch);
        $status = (int) \curl_getinfo($ch, \CURLINFO_RESPONSE_CODE);
        $errNo = \curl_errno($ch);
        $err = \curl_error($ch);
        \curl_close($ch);

        if ($errNo === 23 || $errNo === CURLE_WRITE_ERROR) {
            return ['kind' => 'final', 'result' => ['ok' => false, 'status' => $status, 'body' => '', 'error' => 'body exceeded max bytes']];
        }
        if ($errNo !== 0) {
            return ['kind' => 'final', 'result' => ['ok' => false, 'status' => $status, 'body' => '', 'error' => $err]];
        }
        if ($status >= 300 && $status < 400) {
            $location = $this->lastLocation($url, $status);
            if ($location === '') {
                return ['kind' => 'final', 'result' => ['ok' => false, 'status' => $status, 'body' => '', 'error' => 'redirect without Location']];
            }

            return ['kind' => 'redirect', 'location' => $location];
        }
        if ($status !== 200) {
            return ['kind' => 'final', 'result' => ['ok' => false, 'status' => $status, 'body' => '', 'error' => 'http ' . $status]];
        }

        return ['kind' => 'final', 'result' => ['ok' => true, 'status' => 200, 'body' => $body, 'error' => '']];
    }

    /** Location of the last redirect, re-resolved against the response (simplified). */
    private function lastLocation(string $url, int $status): string
    {
        // curl already consumed the body; re-request headers only for Location
        $ch = \curl_init($url);
        \curl_setopt_array($ch, [
            \CURLOPT_NOBODY => true,
            \CURLOPT_HEADER => true,
            \CURLOPT_CONNECTTIMEOUT => $this->timeoutSeconds,
            \CURLOPT_TIMEOUT => $this->timeoutSeconds,
        ]);
        $headers = (string) \curl_exec($ch);
        \curl_close($ch);
        if (\preg_match('/^Location:\s*(\S+)/mi', $headers, $m) === 1) {
            return \trim($m[1]);
        }

        return '';
    }

    /**
     * The guard every hop passes: scheme, host allow-list, IP-literal shape checks.
     * Returns null when safe, else the rejection reason.
     */
    public function guard(string $url): ?string
    {
        $parts = \parse_url($url);
        if ($parts === false || !isset($parts['scheme'], $parts['host'])) {
            return 'malformed url';
        }
        $scheme = \strtolower((string) $parts['scheme']);
        $host = \strtolower((string) $parts['host']);

        if ($scheme === 'http' && !$this->allowHttp) {
            return 'plain http refused (config allow_http to override consciously)';
        }
        if ($scheme !== 'https' && $scheme !== 'http') {
            return "scheme '{$scheme}' not allowed";
        }
        if ($this->allowHosts !== [] && !\in_array($host, $this->allowHosts, true)) {
            return "host '{$host}' not in allow-list";
        }
        foreach (self::BLOCKED_IP_PREFIXES as $prefix) {
            if (\str_starts_with($host, $prefix)) {
                return "ip-literal host '{$host}' is private/link-range (SSRF guard)";
            }
        }
        // DNS → first A-record also re-checked by shape (hosts that resolve into private space)
        $ip = \gethostbyname($host);
        if (\filter_var($ip, \FILTER_VALIDATE_IP, \FILTER_FLAG_IPV4) !== false) {
            foreach (self::BLOCKED_IP_PREFIXES as $prefix) {
                if (\str_starts_with($ip . '.', $prefix)) {
                    return "host '{$host}' resolves into a private range ({$ip}) — SSRF guard";
                }
            }
        }

        return null;
    }

    /** True when a host is reachable-in-principle for the sync layer. */
    public function isAllowed(string $host): bool
    {
        return $this->guard('https://' . $host) === null;
    }

    private function beginRun(string $url, string $purpose): int
    {
        $now = \gmdate('Y-m-d H:i:s');
        $this->db->run(
            'INSERT INTO provider_runs (provider, status, detail, started_at) VALUES (?, ?, ?, ?)',
            ['http', 'running', \substr($purpose . ' ' . $url, 0, 500), $now]
        );

        return (int) $this->db->scalar('SELECT COALESCE(MAX(id), 0) FROM provider_runs');
    }

    private function finishRun(int $runId, string $status, string $detail): void
    {
        $this->db->run(
            'UPDATE provider_runs SET status = ?, detail = ?, finished_at = ? WHERE id = ?',
            [$status, \substr($detail, 0, 500), \gmdate('Y-m-d H:i:s'), $runId]
        );
    }
}
