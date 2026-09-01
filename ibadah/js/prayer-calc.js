/* ============================================================
   Ibadah — Prayer times engine (vanilla JS, no dependencies)
   حسابات فلكية قياسية (NoAA-style solar calculations)
   + التاريخ الهجري عبر Intl.DateTimeFormat
   ============================================================ */

var PrayerCalc = (function () {
  "use strict";

  /* منهجيات الحساب */
  var METHODS = {
    MWL:    { name: "رابطة العالم الإسلامي",                    fajr: 18,    isha: 17 },
    ISNA:   { name: "الجمعية الإسلامية لأمريكا الشمالية",       fajr: 15,    isha: 15 },
    Egypt:  { name: "الهيئة المصرية العامة للمساحة",           fajr: 19.5,  isha: 17.5 },
    Makkah: { name: "أم القرى — مكة المكرمة",                  fajr: 18.5,  isha: 90 },
    Karachi:{ name: "جامعة العلوم الإسلامية — كراتشي",          fajr: 18,    isha: 18 },
    Tehran: { name: "معهد الجيوفيزياء — طهران",                fajr: 17.7,  isha: 14, maghribAdj: 4.5 },
    Jeddah: { name: "رابطة العالم الإسلامي — جدة",             fajr: 18,    isha: 17 }
  };

  /* ---------- أدوات زاوية ---------- */
  function rad(d) { return d * Math.PI / 180; }
  function deg(r) { return r * 180 / Math.PI; }
  function fixHour(h) { h = h % 24; return h < 0 ? h + 24 : h; }
  function fixAngle(a) { a = a % 360; return a < 0 ? a + 360 : a; }
  function sinc(x) { return Math.sin(rad(x)); }
  function cosc(x) { return Math.cos(rad(x)); }
  function arccosC(x) { return deg(Math.acos(Math.max(-1, Math.min(1, x)))); }
  function arctanC(y, x) { return deg(Math.atan2(y, x)); }

  /* ---------- رقم اليوم اليولياني (بدون ساعات) ---------- */
  function julianDay(y, m, d) {
    if (m <= 2) { y -= 1; m += 12; }
    var A = Math.floor(y / 100);
    var B = 2 - A + Math.floor(A / 4);
    return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + d + B - 1524.5;
  }

  /* ---------- موقع الشمس: الميل وزاوية المعادلة ---------- */
  function sunPosition(jd) {
    var D = jd - 2451545.0;
    var g = fixAngle(357.529 + 0.98560028 * D);
    var q = fixAngle(280.459 + 0.98564736 * D);
    var L = fixAngle(q + 1.915 * Math.sin(rad(g)) + 0.020 * Math.sin(rad(2 * g)));
    var e = 23.439 - 0.00000036 * D;
    var RA = arctanC(cosc(e) * sinc(L), cosc(L)) / 15;
    var decl = deg(Math.asin(Math.max(-1, Math.min(1, sinc(e) * sinc(L)))));
    var EqT = q / 15 - fixHour(RA);
    return { declination: decl, equation: EqT, asc: RA };
  }

  /* ---------- زاوية الساعة لارتفاع معين ---------- */
  function hourAngle(altitude, decl, lat) {
    var c = (sinc(altitude) - sinc(lat) * sinc(decl)) / (cosc(lat) * cosc(decl));
    return arccosC(c); // بالدرجات
  }

  /* ---------- حساب أوقات يوم كامل ---------- */
  function computeDay(date, lat, lng, tzHours, settings) {
    var method = METHODS[settings && settings.method ? settings.method : "MWL"] || METHODS.MWL;
    var madhab = settings && settings.asrMadhab === "Hanafi" ? 1 : 2;

    var jd0 = julianDay(date.getFullYear(), date.getMonth() + 1, date.getDate());
    var jdLocalNoon = jd0 + (12 - tzHours) / 24;
    var pos = sunPosition(jdLocalNoon);
    var decl = pos.declination;
    var E = pos.equation;

    /* ساعة الظهر الشمسية بالتوقيت المحلي (فرق الطول: درجة لكل 4 دقائق) */
    var solarNoon = 12 - E + (15 * tzHours - lng) / 15;
    solarNoon = fixHour(solarNoon + 24); // قيمة عائمة بالساعات

    function clock(hoursFromNoon) {
      return fixHour(solarNoon + hoursFromNoon);
    }

    function altitudeTime(altitude, dir) {
      var H = hourAngle(altitude, decl, lat);
      if (isNaN(H)) return null; // لا توجد صلاة في هذا العرض
      return clock(dir * H / 15);
    }

    var res = {};

    res.fajr = altitudeTime(-method.fajr, -1);
    res.sunrise = altitudeTime(-0.833, -1);
    res.dhuhr = clock(5 / 60); // إضافة دقائق احتياط قليلة بعد الزوال
    res.asr = (function () {
      /* طول الظل: العصر = نسبة ظل k (شافعي k=2، حنفي k=1) */
      var tanD = Math.abs(Math.tan(rad(Math.abs(lat - decl))));
      var alpha = deg(Math.atan(1 / (madhab + tanD))); // موجبة
      var H = hourAngle(alpha, decl, lat);
      if (isNaN(H)) return null;
      return clock(H / 15);
    })();
    res.sunset = altitudeTime(-0.833, 1);
    res.maghrib = (method.maghribAdj ? clock((hourAngle(-0.833, decl, lat) / 15) + method.maghribAdj / 60) : res.sunset);

    if (method.isha === 90) {
      res.isha = res.maghrib === null ? null : fixHour(res.maghrib + 1.5);
    } else {
      res.isha = altitudeTime(-method.isha, 1);
    }

    res.imsak = altitudeTime(-method.fajr - 0.5, -1);

    return res;
  }

  /* ---------- تحويل ساعة عائمة إلى {hour, minute} ---------- */
  function toClock(h) {
    if (h === null || h === undefined || isNaN(h)) return null;
    h = fixHour(h);
    var hours = Math.floor(h);
    var minutes = Math.round((h - hours) * 60);
    if (minutes === 60) { hours = (hours + 1) % 24; minutes = 0; }
    return { hour: hours, minute: minutes };
  }

  function fmt(t, use12) {
    if (!t) return "--:--";
    var h = t.hour, m = String(t.minute).padStart(2, "0");
    if (use12 === false) return String(h).padStart(2, "0") + ":" + m;
    var sfx = h >= 12 ? "م" : "ص";
    h = h % 12; if (h === 0) h = 12;
    return h + ":" + m + " " + sfx;
  }

  /* ---------- إزاحة المنطقة الزمنية للمدينة ---------- */
  function tzOffsetHours(date, tz) {
    try {
      var parts = new Intl.DateTimeFormat("en-US", {
        timeZone: tz || "UTC", hour12: false,
        year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit"
      }).formatToParts(date);
      var map = {};
      parts.forEach(function (p) { map[p.type] = p.value; });
      var local = Date.UTC(map.year, map.month - 1, map.day, map.hour % 24, map.minute);
      var utc = Date.UTC(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), date.getMinutes());
      return Math.round((local - utc) / 3600000 * 2) / 2;
    } catch (e) {
      return 0;
    }
  }

  return {
    METHODS: METHODS,

    getTimes: function (date, city, settings) {
      var tz = tzOffsetHours(date, city && city.tz);
      var raw = computeDay(date, city.lat, city.lng, tz, settings);
      var out = {};
      Object.keys(raw).forEach(function (k) { out[k] = toClock(raw[k]); });
      out.prayerNames = [
        { key: "fajr", ar: "الفجر" },
        { key: "sunrise", ar: "الشروق" },
        { key: "dhuhr", ar: "الظهر" },
        { key: "asr", ar: "العصر" },
        { key: "maghrib", ar: "المغرب" },
        { key: "isha", ar: "العشاء" }
      ];
      return out;
    },

    formatTime: fmt,
    format12: fmt,

    hijriDate: function (date) {
      try {
        var parts = new Intl.DateTimeFormat("ar-SA-u-ca-islamic-umalqura", {
          day: "numeric", month: "long", year: "numeric"
        }).formatToParts(date);
        var d = {};
        parts.forEach(function (p) { d[p.type] = p.value; });
        return (d.day + " " + d.month + " " + d.year + " هـ").replace(/\u200f/g, "");
      } catch (e) {
        return "";
      }
    },

    weekdayAr: function (date) {
      return new Intl.DateTimeFormat("ar", { weekday: "long" }).format(date);
    },

    gregorianAr: function (date) {
      return new Intl.DateTimeFormat("ar", { day: "numeric", month: "long", year: "numeric" }).format(date);
    },

    /* اليوم التالي بعد عدد أيام */
    addDays: function (date, n) {
      var d = new Date(date.getTime());
      d.setDate(d.getDate() + n);
      return d;
    },

    /* اتجاه القبلة (درجة من الشمال) من موقع معين إلى الكعبة */
    qiblaBearing: function (lat, lng) {
      var KABA_LAT = 21.422487, KABA_LNG = 39.826206;
      var phi1 = rad(lat), phi2 = rad(KABA_LAT);
      var dLng = rad(KABA_LNG - lng);
      var y = Math.sin(dLng);
      var x = Math.cos(phi1) * Math.tan(phi2) - Math.sin(phi1) * Math.cos(dLng);
      return (deg(Math.atan2(y, x)) + 360) % 360;
    }
  };
})();

if (typeof window !== "undefined") window.PrayerCalc = PrayerCalc;
