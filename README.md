# Discord Protection Bot (Arabic + English + Obfuscated)

ميزات:
- فلتر سب/كلمات بذيئة (عربي + إنجليزي + كلمات مشفّرة).
- حماية من: **Ban/Kick** غير المصرح، إضافة بوتات، تعديل/حذف الرتب.
- أوامر **Slash** والتفويض فقط لأصحاب الرتب القوية.
- تنبيهات في قناة محددة بالـ ID.

## التشغيل
1) Python 3.10+.
2) ثبت المكتبات:
```bash
pip install -r requirements.txt
```
3) انسخ `config.example.json` إلى `config.json` ثم عدل:
```json
{
  "TOKEN": "PUT_YOUR_TOKEN_HERE",
  "ALERT_CHANNEL_ID": 123456789012345678
}
```
> أو ضع متغير بيئة `DISCORD_TOKEN` بدلًا من `TOKEN`.

4) شغل البوت:
```bash
python bot.py
```

## أوامر السلاش
- `/حماية [channel]` → تفعيل فلتر السب للقناة.
- `/الغاء [channel]` → إلغاء فلتر السب للقناة.
- `/الحالة` → عرض القنوات المحمية.
- `/كلمة_ممنوعة_إضافة word`
- `/كلمة_ممنوعة_إزالة word`
- `/كلمة_ممنوعة_قائمة`

## ملاحظات
- لا تحفظ قائمة الكلمات المضافة بعد إعادة التشغيل (in-memory). لو تبغاها دائمة، أضف حفظ لملف JSON بسهولة.
- تأكد من أن البوت يملك صلاحيات: **View Audit Log, Manage Messages, Moderate Members, Kick/Ban Members, Manage Roles** عند الحاجة.
