<?php

declare(strict_types=1);

/**
 * Console entry point. Kept deliberately tiny: parse argv, build the graph, run one command.
 * (Buyers on shared hosts get `php bin/arcade.php licenses:audit --strict` — no composer needed.)
 *
 * Commands:
 *   licenses:audit [--strict] [--game=slug]   audit the ledger; exit 1 on violations
 */

use Nawras\App;
use Nawras\License\LicenseAuditor;
use Nawras\License\LicenseRepository;

if (\PHP_SAPI !== 'cli') {
    \fwrite(\STDERR, "cli only\n");
    exit(2);
}

require \dirname(__DIR__) . '/src/autoload.php';

$args = \array_slice($argv, 1);
$command = $args[0] ?? null;
$strict = \in_array('--strict', $args, true);
$onlyGame = null;
foreach ($args as $arg) {
    if (\str_starts_with($arg, '--game=')) {
        $onlyGame = \substr($arg, 7);
    }
}

try {
    $app = App::boot();
} catch (\Throwable $e) {
    \fwrite(\STDERR, 'config error: ' . $e->getMessage() . "\n");
    exit(2);
}

if ($command !== 'licenses:audit') {
    \fwrite(\STDERR, "usage: php bin/arcade.php licenses:audit [--strict] [--game=slug]\n");
    exit(2);
}

$repository = new LicenseRepository($app->db());
$auditor = new LicenseAuditor([
    'providers' => (array) (($app->config()['providers'] ?? []) ? array_keys((array) $app->config()['providers']) : []),
]);

$games = $onlyGame !== null
    ? ([$repository->scanGame($onlyGame)] ?? [])
    : $repository->scanAll();

if ($games === [null] || $games === []) {
    \fwrite(\STDERR, "no games matched\n");
    exit(1);
}

$report = $auditor->scanAll($games);

foreach ($report['errors'] as $v) {
    \printf("ERROR   %-14s %s · %s\n", $v['rule'], $v['slug'], $v['message']);
}
foreach ($report['warnings'] as $v) {
    \printf("WARNING %-14s %s · %s\n", $v['rule'], $v['slug'], $v['message']);
}

\fwrite(\STDERR, \sprintf(
    "audited %d game(s): %d error(s), %d warning(s)%s\n",
    $report['games'],
    \count($report['errors']),
    \count($report['warnings']),
    $strict ? ' · strict' : ''
));

if ($report['errors'] !== [] || ($strict && $report['warnings'] !== [])) {
    exit(1);
}
exit(0);
