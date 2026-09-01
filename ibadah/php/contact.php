<?php
/* ============================================================
   Ibadah — PHP endpoint: نموذج الاتصال (اختياري)
   عيّن MAIL_TO إلى بريدك الحقيقي عند النشر على استضافة PHP.
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
$subject = trim($_POST['subject'] ?? 'استفسار عام');
$message = trim($_POST['message'] ?? '');

/* تحقق أساسي */
if ($name === '' || $email === '' || $message === '') {
    http_response_code(422);
    echo json_encode(['ok' => false, 'message' => 'جميع الحقول المطلوبة يجب تعبئتها']);
    exit;
}
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(422);
    echo json_encode(['ok' => false, 'message' => 'البريد الإلكتروني غير صالح']);
    exit;
}

/* تنظيف النصوص */
$name    = htmlspecialchars($name, ENT_QUOTES, 'UTF-8');
$subject = htmlspecialchars($subject, ENT_QUOTES, 'UTF-8');
$message = htmlspecialchars($message, ENT_QUOTES, 'UTF-8');

define('MAIL_TO', 'info@ibadah-center.org'); // ← غيّر هذا

$body = "رسالة جديدة من الموقع\n"
      . "------------------------\n"
      . "الاسم: $name\n"
      . "البريد: $email\n"
      . "الهاتف: $phone\n"
      . "الموضوع: $subject\n"
      . "الرسالة:\n$message\n";

$headers = "From: no-reply@ibadah-center.org\r\n"
         . "Reply-To: $email\r\n"
         . "Content-Type: text/plain; charset=UTF-8\r\n";

if (@mail(MAIL_TO, "اتصال: $subject", $body, $headers)) {
    echo json_encode(['ok' => true, 'message' => 'تم إرسال رسالتك بنجاح']);
} else {
    http_response_code(500);
    echo json_encode(['ok' => false, 'message' => 'تعذر إرسال الرسالة، حاول لاحقاً']);
}
