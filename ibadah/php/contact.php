<?php
/* ============================================================
   Ibadah — PHP endpoint: contact form (optional)
   Set MAIL_TO to your real address when deploying on PHP hosting.
   ============================================================ */

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'message' => 'Method not allowed']);
    exit;
}

$name    = trim($_POST['name'] ?? '');
$email   = trim($_POST['email'] ?? '');
$phone   = trim($_POST['phone'] ?? '');
$subject = trim($_POST['subject'] ?? 'General inquiry');
$message = trim($_POST['message'] ?? '');

/* Basic validation */
if ($name === '' || $email === '' || $message === '') {
    http_response_code(422);
    echo json_encode(['ok' => false, 'message' => 'All required fields must be filled']);
    exit;
}
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(422);
    echo json_encode(['ok' => false, 'message' => 'Invalid email address']);
    exit;
}

/* Enforce sane length limits (protects against abuse) */
if (strlen($name) > 100 || strlen($email) > 254 || strlen($phone) > 30 ||
    strlen($subject) > 150 || strlen($message) > 5000) {
    http_response_code(422);
    echo json_encode(['ok' => false, 'message' => 'One or more fields are too long']);
    exit;
}

/* Sanitize text (XSS-safe output; email is already validated) */
$name    = htmlspecialchars($name, ENT_QUOTES, 'UTF-8');
$phone   = htmlspecialchars($phone, ENT_QUOTES, 'UTF-8');
$subject = htmlspecialchars($subject, ENT_QUOTES, 'UTF-8');
$message = htmlspecialchars($message, ENT_QUOTES, 'UTF-8');

/* Strip CR/LF from fields that could be abused in headers */
$email   = preg_replace('/[\r\n]+/', '', $email);

define('MAIL_TO', 'info@ibadah-center.org'); // ← change this

$body = "New message from the website\n"
      . "------------------------\n"
      . "Name: $name\n"
      . "Email: $email\n"
      . "Phone: $phone\n"
      . "Subject: $subject\n"
      . "Message:\n$message\n";

$headers = "From: no-reply@ibadah-center.org\r\n"
         . "Reply-To: $email\r\n"
         . "Content-Type: text/plain; charset=UTF-8\r\n";

if (@mail(MAIL_TO, "Contact: $subject", $body, $headers)) {
    echo json_encode(['ok' => true, 'message' => 'Your message was sent successfully']);
} else {
    http_response_code(500);
    echo json_encode(['ok' => false, 'message' => 'Could not send the message, please try again later']);
}
