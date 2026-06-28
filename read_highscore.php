<?php
// CORS-Header, damit dein Unity-Spiel von GitHub Pages aus zugreifen darf
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// Verbindung zur PostgreSQL-Datenbank über die Render-Umgebungsvariable
$dbUrl = getenv("DATABASE_URL"); 

if (!$dbUrl) {
    echo json_encode(["error" => "Datenbank-Konfiguration fehlt"]);
    exit;
}

try {
    // Datenbank-URL parsen
    $dbopts = parse_url($dbUrl);
    $dsn = "pgsql:host=" . $dbopts["host"] . ";port=" . $dbopts["port"] . ";dbname=" . ltrim($dbopts["path"], '/');
    $pdo = new PDO($dsn, $dbopts["user"], $dbopts["pass"], [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
    ]);

    // Die besten 6 Einträge holen
    $stmt = $pdo->query("SELECT name, points FROM highscores ORDER BY points DESC LIMIT 6");
    $scores = $stmt->fetchAll();

    // Falls die Datenbank leer ist oder weniger als 6 Einträge hat, mit "-" auffüllen
    while (count($scores) < 6) {
        $scores[] = ["points" => "-", "name" => "-"];
    }

    echo json_encode(["scores" => $scores]);

} catch (PDOException $e) {
    echo json_encode(["error" => "Datenbankfehler: " . $e->getMessage()]);
}
?>
