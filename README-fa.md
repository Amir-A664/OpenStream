# اوپن استریم (`opst`)

[English](README.md) | فارسی

اوپن استریم یک ابزار کوچک برای لینوکس است که OpenVPN را داخل یک فضای نام شبکه‌ی جداگانه اجرا می‌کند و اتصال وی‌پی‌ان را به شکل یک پروکسی SOCKS5 در اختیار برنامه‌ها می‌گذارد.

ایده ساده است: مسیر اینترنت اصلی سیستم دست‌نخورده می‌ماند. فقط برنامه‌هایی که روی نشانی SOCKS5 تنظیم شده‌اند از مسیر وی‌پی‌ان عبور می‌کنند؛ بقیه‌ی ترافیک سیستم همان مسیر معمول خودش را دارد.

## اوپن استریم چگونه کار می‌کند؟

اوپن استریم یک فضای نام شبکه با نام `opstns` می‌سازد، OpenVPN را داخل همان محیط اجرا می‌کند، سپس `microsocks` را هم در همان فضای جداگانه بالا می‌آورد. بعد روی سیستم اصلی، با کمک `socat` یک شنونده‌ی محلی یا قابل‌دسترسی از شبکه‌ی محلی ساخته می‌شود و اتصال‌ها به سرور SOCKS داخل فضای نام شبکه فرستاده می‌شوند.

نشانی پیش‌فرض پس از نصب معمولاً این است:

```text
socks5h://127.0.0.1:2086
```

پورت ثابت و اجباری نیست. هنگام نصب، نصب‌کننده از کاربر می‌پرسد کدام پورت برای SOCKS5 استفاده شود و همان مقدار را در این فایل ذخیره می‌کند:

```text
/etc/opst/config.toml
```

## اوپن استریم چه چیزی نیست؟

اوپن استریم ارائه‌دهنده‌ی وی‌پی‌ان نیست، اطلاعات ورود یا فایل آماده‌ی وی‌پی‌ان همراه خودش ندارد، کل ترافیک سیستم را خودکار از وی‌پی‌ان رد نمی‌کند، و مسیر پیش‌فرض شبکه‌ی سیستم را تغییر نمی‌دهد. هر برنامه‌ای که قرار است از وی‌پی‌ان استفاده کند، باید جداگانه روی پروکسی SOCKS5 تنظیم شود.

این نسخه برای سامانه‌های لینوکسی شبیه Debian و Ubuntu ساخته شده و به ابزارهایی مثل `systemd`، `iproute2`، `iptables`، OpenVPN، `microsocks` و `socat` نیاز دارد.

## نصب

دستورات زیر رو به ترتیب اجرا کنید: (طبیعتابرای نصب اولیه از گیت‌هاب و نصب پکیج‌های مورد نیاز، باید بار اول خودتون به اینترنت آزاد دسترسی داشته باشید!)

```sh
git clone https://github.com/Amir-A664/OpenStream.git
cd OpenStream
sudo ./install.sh
```

فایل Installer این کارها را انجام می‌دهد:

1. پورت SOCKS5 را می‌پرسد؛
2. وابستگی‌های اجرایی را بررسی می‌کند؛
3. اگر چیزی کم باشد، پیشنهاد نصب بسته‌های لازم با `apt` می‌دهد (طبیعتا اگر قرار است از این پروژه روی توزیع‌های دیگه‌ی لینوکسی که پکیج منیجر apt ندارند استفاده کنید، خودتان وابستگی‌ها را مجرا نصب کنید)؛
4. پوشه‌ی زیر را برای قرار دادن فایل‌های `.ovpn` می‌سازد:

```text
/home/<username>/Desktop/opst/
```

5. دستور `opst` و واحدهای `systemd` را نصب می‌کند.

دیپندسی (وابستگی) های لازم برای اجرای اوپن استریم:

```text
openvpn, ip, iptables, socat, microsocks, curl, systemctl
```

اگر می‍‌خواهید دستی پکیج‌های دیپندسی را روی Debian و Ubuntu نصب کنید:

```sh
sudo apt install openvpn iproute2 iptables socat microsocks curl systemd
```

## اضافه کردن نمایه‌های OpenVPN

یک یا چند فایل `.ovpn` را داخل این پوشه قرار دهید:

```text
/home/<username>/Desktop/opst/
```

بعد اجرا کنید:

```sh
opst on
```

اوپن استریم این پوشه را بررسی می‌کند، فایل‌های جدید را داخل مسیر زیر کپی و نگهداری می‌کند:

```text
/var/lib/opst/profiles/
```

سپس اوپن استریم به طور خودکار روش احراز هویت را تشخیص می‌دهد، فقط در صورت نیاز نام کاربری و گذرواژه می‌پرسد، فایل `.ovpn` را برای سازگاری با OpenVPN 2.6.x اصلاح می‌کند، و اجازه می‌دهد نمایه‌ی فعال انتخاب شود.

روش‌های احراز هویت پشتیبانی‌شده در نسخه `v1.0.0`:

```text
username/password
certificate-based
hybrid username/password + certificate
static key / tls-auth / tls-crypt
```

## اجرای حالت محلی

```sh
opst on
```

در این حالت، شنونده‌ی پروکسی روی این نشانی فعال می‌شود:

```text
127.0.0.1:<configured-port>
```

برای آزمایش:

```sh
opst test
```

یا به شکل دستی:

```sh
curl --proxy socks5h://127.0.0.1:2086 https://ifconfig.me
```

به جای `2086` همان پورتی را بگذارید که هنگام نصب انتخاب شده است.

## اجرای حالت شبکه‌ی محلی

```sh
opst on --lan
```

در این حالت، شنونده روی این نشانی فعال می‌شود:

```text
0.0.0.0:<configured-port>
```

اوپن استریم هشداری شبیه این نشان می‌دهد:

```text
WARNING: LAN mode exposes SOCKS5 on 0.0.0.0:2086
Only use this on trusted networks.
```

حالا شمابه سادگی می‌توانید با روشن نگه‍داشتن اوپن استریم روی لپ‌تاپ یا کامپیوترتون، داخل تلگرام گوشی یک پروکسی SOCKS5 با ایپی سیستم‌تان و پورت مورد انتخابتون بسازید و به تلگرام متصل بشوید! (همین کار رو می‌تونید با نرم افزار V2rayNG روی گوشی هم انجام بدهید تا تمام گوشی‌تون به اینترنت دسترسی داشته باشه.)
حالت شبکه‌ی محلی را روی شبکه‌های عمومی، خوابگاه، کافه، فرودگاه، یا هر شبکه‌ای که قابل اعتماد نیست روشن نکنید. این حالت عملاً یک درگاه به نمایه‌ی وی‌پی‌ان شما باز می‌کند که نباید بی‌حساب‌وکتاب باز بماند.

## دستورها

```sh
opst on
opst on --lan
opst off
opst restart
opst restart --lan
opst status
opst current
opst use
opst profiles
opst add
opst remove
opst test
opst logs
opst logs openvpn
sudo opst uninstall
```

## آزمایش اتصال

```sh
opst test
```

این دستور در عمل چنین کاری انجام می‌دهد:

```sh
curl --proxy socks5h://127.0.0.1:<configured-port> https://ifconfig.me
```

## دیدن گزارش‌ها

```sh
opst logs
opst logs setup
opst logs openvpn
opst logs socks
opst logs localproxy
```

برای بررسی مستقیم وضعیت سرویس‌ها:

```sh
systemctl status opst-setup.service --no-pager -l
systemctl status opst-openvpn.service --no-pager -l
systemctl status opst-socks.service --no-pager -l
systemctl status opst-localproxy.service --no-pager -l
```

## حذف کامل

```sh
sudo opst uninstall
```

یا از داخل مخزن پروژه:

```sh
sudo ./uninstall.sh
```

حذف‌کننده، فایل‌های سیستمی، واحدهای `systemd`، وضعیت اجرایی، نمایه‌های نگهداری‌شده، و فضای نام شبکه را پاک می‌کند. پوشه‌ی اصلی فایل‌های `.ovpn` به‌صورت پیش‌فرض حذف نمی‌شود، چون ممکن است فایل‌های اصلی کاربر داخل آن باشد.

## حمایت مالی

اگر اوپن استریم برای شما مفید بود، می‌توانید با کمک مالی کریپتویی از ادامه‌ی توسعه‌ی پروژه حمایت کنید:

```text
Bitcoin (BTC): bc1ql05zalkxftmrxwp2d6y9u97e3ypg6n8yfzpp2g
Ethereum / ERC-20 / (Ethereum mainnet, Binance Smart Chain, Arbitrum, Optimism, Base, Polygon, and other ERC-20/L2 networks): 0x920986fee228a8d62b58a9a25fece7aafb469e70
Solana (SOL / SPL): D6sFh8xjgnfLe2p3w55m68ERwt8gaMYDcNZaqfhUrvQ8
Litecoin (LTC): ltc1qzl3lyaz83xnnurr2rwge5smgg8e3nma5fwk632
Zcash (ZEC): t1QX9A83h4GxnZsXbqWbx8SCbprkwductoA
Ton (TON): UQBoXYOLS8sn4YBO0ojc042uhGnHyyFuuwJPI7ArBZjOhoq9
```

## نکات امنیتی

فایل واقعی `.ovpn` را اگر شامل کلید خصوصی، گواهی خصوصی، نام میزبان ارائه‌دهنده، نام کاربری، گذرواژه، یا مسیر فایل احراز هویت است، وارد مخزن نکنید. این فایل‌ها هم تحت هیچ شرایطی نباید وارد GitHub شوند:

```text
/etc/openvpn/opst/auth/*.txt
*.key
*.pem
*.p12
*.pfx
```

اوپن استریم برای نمایه‌هایی که نام کاربری و گذرواژه می‌خواهند، فایل احراز هویت جداگانه می‌سازد:

```text
/etc/openvpn/opst/auth/<profile-id>.txt
```

مالکیت و سطح دسترسی این فایل باید چنین باشد:

```text
root:root
0600
```

پاینده ایران.
