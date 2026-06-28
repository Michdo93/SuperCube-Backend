<?php
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With");
header("Access-Control-Allow-Methods: POST, GET, OPTIONS");
header("Content-Type: application/json; charset=UTF-8");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0); // CORS Preflight abfangen
}

$dbUrl = getenv("DATABASE_URL");
if (!$dbUrl) {
    echo json_encode(["status" => "error", "message" => "Datenbank-Konfiguration fehlt"]);
    exit;
}

try {
    $dbopts = parse_url($dbUrl);
    $dsn = "pgsql:host=" . $dbopts["host"] . ";port=" . $dbopts["port"] . ";dbname=" . ltrim($dbopts["path"], '/');
    $pdo = new PDO($dsn, $dbopts["user"], $dbopts["pass"], [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
    ]);

    // Daten aus Unity holen (unterstützt POST und GET via $_REQUEST)
    $name = isset($_REQUEST['name']) ? trim($_REQUEST['name']) : '';
    $points = isset($_REQUEST['points']) ? (int)$_REQUEST['points'] : 0;

    // Einfache Validierung
    if (!empty($name) && $points > 0) {
        // SQL-Injection-sicheres Einfügen
        $stmt = $pdo->prepare("INSERT INTO highscores (name, points) VALUES (:name, :points)");
        $stmt->execute(['name' => $name, 'points' => $points]);
        
        echo json_encode(["status" => "success", "message" => "Highscore erfolgreich gespeichert"]);
    } else {
        echo json_encode(["status" => "invalid_data", "message" => "Name oder Punkte ungültig"]);
    }

} catch (PDOException $e) {
    echo json_encode(["status" => "error", "message" => "Datenbankfehler: " . $e->getMessage()]);
}
?>
