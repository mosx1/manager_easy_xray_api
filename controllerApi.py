import subprocess, json, os

from app_config import load_config
from methods.xray.config_server import ConfigServer
from methods.xray.general import EasyXray, EasyXrayError


def _client_link_config(user_id, public_key, server_name, short_id, host_name):
    return {
        "log": {},
        "remarks": f"🍜 Выгодный ВПН - {host_name}",
        "inbounds": [
            {
                "settings": {
                    "udp": True,
                    "userLevel": 8,
                    "auth": "noauth",
                },
                "listen": "127.0.0.1",
                "port": 10808,
                "tag": "socks",
                "protocol": "socks",
            },
            {
                "settings": {
                    "userLevel": 8,
                    "udp": True,
                    "auth": "noauth",
                },
                "listen": "127.0.0.1",
                "port": 1087,
                "tag": "directSocks",
                "protocol": "socks",
            },
            {
                "settings": {
                    "address": "[::1]",
                },
                "listen": "[::1]",
                "port": 62789,
                "tag": "api",
                "protocol": "dokodemo-door",
            },
        ],
        "outbounds": [
            {
                "tag": "proxy",
                "protocol": "vless",
                "streamSettings": {
                    "sockopt": {
                        "dialerProxy": "fragment",
                        "tcpNoDelay": True,
                    },
                    "network": "tcp",
                    "security": "reality",
                    "tcpSettings": {
                        "header": {
                            "type": "none",
                        },
                    },
                    "realitySettings": {
                        "publicKey": public_key,
                        "serverName": server_name,
                        "show": False,
                        "mldsa65Verify": "",
                        "spiderX": "",
                        "shortId": short_id,
                        "fingerprint": "firefox",
                    },
                },
                "settings": {
                    "vnext": [
                        {
                            "port": 443,
                            "users": [
                                {
                                    "encryption": "none",
                                    "flow": "xtls-rprx-vision",
                                    "id": user_id,
                                    "level": 8,
                                    "email": "",
                                },
                            ],
                            "address": host_name,
                        },
                    ],
                },
                "mux": {
                    "concurrency": 50,
                    "xudpConcurrency": 128,
                    "xudpProxyUDP443": "allow",
                    "enabled": False,
                },
            },
            {
                "settings": {
                    "userLevel": 8,
                    "fragment": {
                        "length": "80-250",
                        "interval": "10-100",
                        "packets": "tlshello",
                    },
                },
                "streamSettings": {
                    "sockopt": {
                        "tcpNoDelay": True,
                    },
                },
                "tag": "fragment",
                "protocol": "freedom",
            },
        ],
        "api": {
            "tag": "api",
            "services": [
                "StatsService",
            ],
        },
        "dns": {
            "queryStrategy": "UseIP",
            "servers": [
                {
                    "address": "8.8.8.8",
                    "skipFallback": False,
                },
            ],
            "tag": "dnsQuery",
            "disableCache": True,
            "disableFallbackIfMatch": True,
            "hosts": {
                "dns.quad9.net": [
                    "9.9.9.9",
                    "149.112.112.112",
                    "2620:fe::fe",
                    "2620:fe::9",
                ],
                "one.one.one.one": [
                    "1.1.1.1",
                    "1.0.0.1",
                    "2606:4700:4700::1111",
                    "2606:4700:4700::1001",
                ],
                "dns.google": [
                    "8.8.8.8",
                    "8.8.4.4",
                    "2001:4860:4860::8888",
                    "2001:4860:4860::8844",
                ],
                "cloudflare-dns.com": [
                    "104.16.248.249",
                    "104.16.249.249",
                    "2606:4700::6810:f8f9",
                    "2606:4700::6810:f9f9",
                ],
                "dns.alidns.com": [
                    "223.5.5.5",
                    "223.6.6.6",
                    "2400:3200::1",
                    "2400:3200:baba::1",
                ],
                "dns.cloudflare.com": [
                    "104.16.132.229",
                    "104.16.133.229",
                    "2606:4700::6810:84e5",
                    "2606:4700::6810:85e5",
                ],
                "common.dot.dns.yandex.net": [
                    "77.88.8.8",
                    "77.88.8.1",
                    "2a02:6b8::feed:0ff",
                    "2a02:6b8:0:1::feed:0ff",
                ],
                "dot.pub": [
                    "1.12.12.12",
                    "120.53.53.53",
                ],
            },
            "disableFallback": True,
        },
        "stats": {},
        "routing": {
            "balancers": [],
            "domainStrategy": "AsIs",
            "rules": [
                {
                    
                    "type": "field",
                    "domain": [
                        "domain:ivi.ru",
                        "domain:acint.net",
                        "domain:adhigh.net",
                        "domain:admon.pro",
                        "domain:adriver.ru",
                        "domain:adsp.io",
                        "domain:adspector.io",
                        "domain:adspend.space",
                        "domain:afp.ai",
                        "domain:aidata.io",
                        "domain:betweendigital.com",
                        "domain:bidderstack.com",
                        "domain:bidster.net",
                        "domain:bidvol.com",
                        "domain:buzzoola.com",
                        "domain:digitaltarget.ru",
                        "domain:dynotech.io",
                        "domain:getads.ru",
                        "domain:getshop.tv",
                        "domain:giftclick.ru",
                        "domain:gpmdata.ru",
                        "domain:kimberlite.io",
                        "domain:kombinat.digital",
                        "domain:linkssp.ru",
                        "domain:link-platform.ru",
                        "domain:lotus-dsp.ru",
                        "domain:melvad.com",
                        "domain:new-programmatic.com",
                        "domain:ohmy.bid",
                        "domain:onetarget.ru",
                        "domain:opendsp.ru",
                        "domain:otclick-adv.ru",
                        "domain:otm-r.com",
                        "domain:prodmp.ru",
                        "domain:rutarget.ru",
                        "domain:sspnet.tech",
                        "domain:statad.ru",
                        "domain:targetads.io",
                        "domain:upravel.com",
                        "domain:utraff.com",
                        "domain:ussp.io",
                        "domain:yadro.ru",
                        "domain:1c-bitrix.ru",
                        "domain:1cfresh.com",
                        "domain:1cloud.ru",
                        "domain:1internet.tv",
                        "domain:2gis.ae",
                        "domain:2gis.am",
                        "domain:2gis.az",
                        "domain:2gis.by",
                        "domain:2gis.com",
                        "domain:2gis.com.cy",
                        "domain:2gis.cz",
                        "domain:2gis.ge",
                        "domain:2gis.kg",
                        "domain:2gis.kz",
                        "domain:2gis.ru",
                        "domain:2gis.tj",
                        "domain:2gis.ua",
                        "domain:2gis.uz",
                        "domain:2ip.ru",
                        "domain:47news.ru",
                        "domain:4meeting.me",
                        "domain:5ka.ru",
                        "domain:5post.market",
                        "domain:abr.ru",
                        "domain:animego.me",
                        "domain:aclub.ru",
                        "domain:adfox.ru",
                        "domain:admetrica.ru",
                        "domain:adygeya.ru",
                        "domain:aeroflot.ru",
                        "domain:aif.ru",
                        "domain:alfa-bank.com",
                        "domain:alfa-bank.ru",
                        "domain:alfa-finance.com",
                        "domain:alfa-fx.com",
                        "domain:alfa-pc.com",
                        "domain:alfa-usa.com",
                        "domain:alfabank.com",
                        "domain:alfabank.ru",
                        "domain:alfafinance.biz",
                        "domain:alfafinance.ru",
                        "domain:alfafuture.com",
                        "domain:alfafuture.ru",
                        "domain:alfafx.com",
                        "domain:alfaleasing.ru",
                        "domain:alfaprivate.com",
                        "domain:alformacap.com",
                        "domain:alformacapital.com",
                        "domain:altai.ru",
                        "domain:amur.ru",
                        "domain:anytimeru.com",
                        "domain:arkhangelsk.ru",
                        "domain:astrakhan.ru",
                        "domain:auth-nsdi.ru",
                        "domain:auto.ru",
                        "domain:av.ru",
                        "domain:avito.ru",
                        "domain:avito.st",
                        "domain:baltbank.ru",
                        "domain:banka-ui.dev",
                        "domain:banki.ru",
                        "domain:bankline.ru",
                        "domain:bashkiria.ru",
                        "domain:beeline.ru",
                        "domain:belgorod.ru",
                        "domain:beta-bank.com",
                        "domain:bir.ru",
                        "domain:bitrix24.ru",
                        "domain:bronevik.com",
                        "domain:bryansk.ru",
                        "domain:bumlam.com",
                        "domain:burgerkingrus.ru",
                        "domain:buryatia.ru",
                        "domain:chgtrk.ru",
                        "domain:cbg.ru",
                        "domain:cbr.ru",
                        "domain:cdn-tinkoff.ru",
                        "domain:cdn-vk.ru",
                        "domain:chel.ru",
                        "domain:chelyabinsk.ru",
                        "domain:chita.ru",
                        "domain:chizhik.club",
                        "domain:chukotka.ru",
                        "domain:chuvashia.ru",
                        "domain:cikrf.ru",
                        "domain:citydrive.ru",
                        "domain:clstorage.net",
                        "domain:credistory.ru",
                        "domain:crimea.ru",
                        "domain:csat.ru",
                        "domain:cap.ru",
                        "domain:cscampus.ru",
                        "domain:dagestan.ru",
                        "domain:dbankcloud.ru",
                        "domain:dbo-dengi.online",
                        "domain:dellin.ru",
                        "domain:dixy.ru",
                        "domain:dnevnik.ru",
                        "domain:dns-shop.ru",
                        "domain:dodopizza.ru",
                        "domain:dom.ru",
                        "domain:domclick.ru",
                        "domain:donationalerts.com",
                        "domain:drive2.ru",
                        "domain:drweb.ru",
                        "domain:dzen.ru",
                        "domain:dzeninfra.ru",
                        "domain:e5.ru",
                        "domain:ebs.ru",
                        "domain:edadeal.io",
                        "domain:edadeal.ru",
                        "domain:edu.ru",
                        "domain:ekburg.ru",
                        "domain:emias.info",
                        "domain:fastvps.ru",
                        "domain:finuslugi.ru",
                        "domain:fivepost.ru",
                        "domain:fix-price.com",
                        "domain:flypobeda.ru",
                        "domain:forbes.ru",
                        "domain:freestylediabetes.ru",
                        "domain:gazeta.ru",
                        "domain:gazprombank.ru",
                        "domain:gazprombank.tech",
                        "domain:gazprompay.ru",
                        "domain:gismeteo.ru",
                        "domain:gorodpay.ru",
                        "domain:goskey.ru",
                        "domain:gosuslugi.ru",
                        "domain:gov.ru",
                        "domain:government.ru",
                        "domain:gpb.ru",
                        "domain:gpmdi.ru",
                        "domain:grfc.ru",
                        "domain:grozny.ru",
                        "domain:gu-st.ru",
                        "domain:hematonix.ru",
                        "domain:hh.ru",
                        "domain:lg.com",
                        "domain:i-ola.ru",
                        "domain:ican-sinocare.ru",
                        "domain:idx5.ru",
                        "domain:ifconfig.me",
                        "domain:imgsmail.ru",
                        "domain:investalfabank.com",
                        "domain:ip.sb",
                        "domain:ipapi.is",
                        "domain:ipify.org",
                        "domain:iplocate.io",
                        "domain:irk.ru",
                        "domain:irkutsk.ru",
                        "domain:ivanovo.ru",
                        "domain:iz.ru",
                        "domain:izbirkom.ru",
                        "domain:izhevsk.ru",
                        "domain:jamal.ru",
                        "domain:jar.ru",
                        "domain:jivo.ru",
                        "domain:jivochat.com",
                        "domain:jivosite.com",
                        "domain:jx5.ru",
                        "domain:kalmykia.ru",
                        "domain:kaluga.ru",
                        "domain:kamchatka.ru",
                        "domain:karelia.ru",
                        "domain:kaspersky.com",
                        "domain:kaspersky.ru",
                        "domain:kazan.ru",
                        "domain:kazanexpress.ru",
                        "domain:kchr.ru",
                        "domain:kemerovo.ru",
                        "domain:khabarovsk.ru",
                        "domain:khakassia.ru",
                        "domain:khv.ru",
                        "domain:kinopoisk.ru",
                        "domain:kirov.ru",
                        "domain:koenig.ru",
                        "domain:kommersant.ru",
                        "domain:kontur.host",
                        "domain:kontur.ru",
                        "domain:kostroma.ru",
                        "domain:kp.ru",
                        "domain:krasnodar.su",
                        "domain:krasnoyarsk.ru",
                        "domain:krasyar.ru",
                        "domain:krd.ru",
                        "domain:kremlin.ru",
                        "domain:kuban.ru",
                        "domain:kuper.ru",
                        "domain:kurgan.ru",
                        "domain:kursk.ru",
                        "domain:lead-pro2023.online",
                        "domain:lemanapro.ru",
                        "domain:lenta.com",
                        "domain:lenta.ru",
                        "domain:lipetsk.ru",
                        "domain:lmru.tech",
                        "domain:lumiflex.ru",
                        "domain:magadan.ru",
                        "domain:magnit.ru",
                        "domain:mail.ru",
                        "domain:mari-el.ru",
                        "domain:mari.ru",
                        "domain:marine.ru",
                        "domain:max.ru",
                        "domain:medtrum.eu",
                        "domain:medtrum.ru",
                        "domain:megafon.ru",
                        "domain:megamarket.ru",
                        "domain:megamarket.tech",
                        "domain:memealerts.com",
                        "domain:mgfoms.ru",
                        "domain:mil.ru",
                        "domain:mirpayonline.ru",
                        "domain:miya-news.online",
                        "domain:mm.ru",
                        "domain:mnogolososya.ru",
                        "domain:moex.com",
                        "domain:mordovia.ru",
                        "domain:mos.ru",
                        "domain:mosreg.ru",
                        "domain:motivtelecom.ru",
                        "domain:mradx.net",
                        "domain:mts.ru",
                        "domain:mtsdengi.ru",
                        "domain:murmansk.ru",
                        "domain:mustproxy.tech",
                        "domain:mvk.com",
                        "domain:myapelsin.ru",
                        "domain:mycdn.me",
                        "domain:mymts.ru",
                        "domain:nalchik.ru",
                        "domain:nalog.ru",
                        "domain:naydex.net",
                        "domain:nbki.ru",
                        "domain:netmonet.co",
                        "domain:nn.ru",
                        "domain:nov.ru",
                        "domain:novosibirsk.ru",
                        "domain:nsk.ru",
                        "domain:nspk.ru",
                        "domain:ok.ru",
                        "domain:okcdn.ru",
                        "domain:okko.sport",
                        "domain:okko.tv",
                        "domain:okolo.app",
                        "domain:omsk.ru",
                        "domain:onef.pro",
                        "domain:oneme.ru",
                        "domain:orb.ru",
                        "domain:oryol.ru",
                        "domain:ozon.ru",
                        "domain:ozone.ru",
                        "domain:ozonru.me",
                        "domain:ozonusercontent.com",
                        "domain:penza.ru",
                        "domain:perekrestok.ru",
                        "domain:perm.ru",
                        "domain:pervye.ru",
                        "domain:pochta.ru",
                        "domain:programmatica.com",
                        "domain:psk",
                        "domain:psk.ru",
                        "domain:pskov.ru",
                        "domain:ptz.ru",
                        "domain:qms.ru",
                        "domain:rambler-co.ru",
                        "domain:rambler.ru",
                        "domain:rbc.ru",
                        "domain:rchuv.ru",
                        "domain:reg.ru",
                        "domain:res-nsdi.ru",
                        "domain:retagro.com",
                        "domain:rg.ru",
                        "domain:ria.ru",
                        "domain:rkomi.ru",
                        "domain:rnd.ru",
                        "domain:rostaxi.org",
                        "domain:rostelecom.ru",
                        "domain:rshb.ru",
                        "domain:rsscenter.cloud",
                        "domain:rt.ru",
                        "domain:rtbcdn.ru",
                        "domain:russiacalling.com",
                        "domain:rustore.ru",
                        "domain:rutube.ru",
                        "domain:rutubelist.ru",
                        "domain:ruwiki.ru",
                        "domain:ryazan.ru",
                        "domain:rzd-bonus.ru",
                        "domain:rzd.ru",
                        "domain:sakhalin.ru",
                        "domain:samara.ru",
                        "domain:samokat.ru",
                        "domain:saratov.ru",
                        "domain:sbermarket.ru",
                        "domain:sbermegamarket.ru",
                        "domain:sberbank.ru",
                        "domain:sbrf.ru",
                        "domain:sbermarketing.ru",
                        "domain:sbpgpb.ru",
                        "domain:sdk-api.apptracer.ru",
                        "domain:sev.ru",
                        "domain:sevastopol.ru",
                        "domain:simbirsk.ru",
                        "domain:sirena-travel.ru",
                        "domain:sistema-capital.com",
                        "domain:smolensk.ru",
                        "domain:spb.ru",
                        "domain:spvb.ru",
                        "domain:sravni.ru",
                        "domain:static-storage.net",
                        "domain:stavropol.ru",
                        "domain:studilka.ru",
                        "domain:stv.ru",
                        "domain:surgut.ru",
                        "domain:svoy.academy",
                        "domain:t-j.ru",
                        "domain:t2.ru",
                        "domain:tambov.ru",
                        "domain:tamtam.chat",
                        "domain:tank-online.com",
                        "domain:tatarstan.ru",
                        "domain:taximaxim.ru",
                        "domain:taxsee.com",
                        "domain:tbank-online.com",
                        "domain:tele2.ru",
                        "domain:tildaapi.com",
                        "domain:timeweb.cloud",
                        "domain:timeweb.com",
                        "domain:tips.tips",
                        "domain:tns-counter.ru",
                        "domain:tnt-online.ru",
                        "domain:tochka-tech.com",
                        "domain:tochka.com",
                        "domain:tom.ru",
                        "domain:tomsk.ru",
                        "domain:topdelivery.ru",
                        "domain:trbcdn.net",
                        "domain:tsaritsyn.ru",
                        "domain:tsk.ru",
                        "domain:tsx.x5static.net",
                        "domain:tu-tu.ru",
                        "domain:tula.ru",
                        "domain:turbopages.org",
                        "domain:tutu.ru",
                        "domain:tuva.ru",
                        "domain:tver.ru",
                        "domain:tyumen.ru",
                        "domain:udm.ru",
                        "domain:udmurtia.ru",
                        "domain:ulan-ude.ru",
                        "domain:usedesk.ru",
                        "domain:userapi.com",
                        "domain:uxfeedback.ru",
                        "domain:vgtrk.ru",
                        "domain:victoria-group.ru",
                        "domain:vk-analytics.ru",
                        "domain:vk-apps.com",
                        "domain:vk-apps.ru",
                        "domain:vk-cdn.me",
                        "domain:vk-cdn.net",
                        "domain:vk-portal.net",
                        "domain:vk.cc",
                        "domain:vk.com",
                        "domain:vk.company",
                        "domain:vk.design",
                        "domain:vk.link",
                        "domain:vk.me",
                        "domain:vk.ru",
                        "domain:vk.team",
                        "domain:vkcache.com",
                        "domain:vkcloud-static.ru",
                        "domain:vkgo.app",
                        "domain:vklive.app",
                        "domain:vkmessenger.app",
                        "domain:vkmessenger.com",
                        "domain:vkontakte.ru",
                        "domain:vkuser.net",
                        "domain:vkuseraudio.com",
                        "domain:vkuseraudio.net",
                        "domain:vkuseraudio.ru",
                        "domain:vkusercdn.ru",
                        "domain:vkuserlive.net",
                        "domain:vkuserphoto.ru",
                        "domain:vkuservideo.com",
                        "domain:vkuservideo.net",
                        "domain:vkuservideo.ru",
                        "domain:vkusnoitochka.ru",
                        "domain:vkusvill.ru",
                        "domain:vkvideo.ru",
                        "domain:vl.ru",
                        "domain:vladikavkaz.ru",
                        "domain:vladimir.ru",
                        "domain:vladivostok.ru",
                        "domain:vlg.ru",
                        "domain:volgograd.ru",
                        "domain:vologda.ru",
                        "domain:voronezh.ru",
                        "domain:vrn.ru",
                        "domain:vtb-grants.fut.ru",
                        "domain:vtb-liga.fut.ru",
                        "domain:vtb-russia.com",
                        "domain:vtb.bank.in",
                        "domain:vtb.com",
                        "domain:vtb.corp.ru",
                        "domain:vtb.digital",
                        "domain:vtb.fut.ru",
                        "domain:vtb.promo",
                        "domain:vtb.ru",
                        "domain:vtb24.com",
                        "domain:vtb24.ru",
                        "domain:vtbcareer.com",
                        "domain:vtbfamily.ru",
                        "domain:vtbindia.com",
                        "domain:vtbkep.site",
                        "domain:vtbpartners.com",
                        "domain:vtbrussia.com",
                        "domain:vtbrussia.ru",
                        "domain:vtbstrana.ru",
                        "domain:vyatka.ru",
                        "domain:vivox.com",
                        "domain:wb.ru",
                        "domain:wbbasket.ru",
                        "domain:weborama-tech.ru",
                        "domain:weborama.fr",
                        "domain:webvisor.com",
                        "domain:webvisor.org",
                        "domain:whoosh.bike",
                        "domain:wildberries.ru",
                        "domain:windsurf.com",
                        "domain:wink.ru",
                        "domain:x5.ru",
                        "domain:x5.tech",
                        "domain:x5club.ru",
                        "domain:x5id.ru",
                        "domain:x5l.ru",
                        "domain:x5paket.ru",
                        "domain:x5q.ru",
                        "domain:xn----7sb7akeedqd.xn--p1ai",
                        "domain:xn--80aacoonefzg3am8b1fsb.xn--p1ai",
                        "domain:xn--80acgfbsl1azdqr.xn--p1ai",
                        "domain:xn--80ajghhoc2aj1c8b.xn--p1ai",
                        "domain:xn--90ab2c.xn--p1ai",
                        "domain:xn--90acagbhgpca7c8c7f.xn--p1ai",
                        "domain:xn--90aifd0aza.site",
                        "domain:xn--90aivcdt6dxbc.xn--p1ai",
                        "domain:xn--b1aew.xn--p1ai",
                        "domain:xn--d1acpjx3f.xn--p1ai",
                        "domain:ya.ru",
                        "domain:yads.tech",
                        "domain:yakutia.ru",
                        "domain:yamal.ru",
                        "domain:yandex",
                        "domain:yandex-bank.net",
                        "domain:yandex-team.ru",
                        "domain:yandex.aero",
                        "domain:yandex.az",
                        "domain:yandex.by",
                        "domain:yandex.cloud",
                        "domain:yandex.co.il",
                        "domain:yandex.com",
                        "domain:yandex.com.am",
                        "domain:yandex.com.ge",
                        "domain:yandex.com.ru",
                        "domain:yandex.com.tr",
                        "domain:yandex.com.ua",
                        "domain:yandex.de",
                        "domain:yandex.ee",
                        "domain:yandex.eu",
                        "domain:yandex.fi",
                        "domain:yandex.fr",
                        "domain:yandex.jobs",
                        "domain:yandex.kg",
                        "domain:yandex.kz",
                        "domain:yandex.lt",
                        "domain:yandex.lv",
                        "domain:yandex.md",
                        "domain:yandex.net",
                        "domain:yandex.org",
                        "domain:yandex.pl",
                        "domain:yandex.ru",
                        "domain:yandex.st",
                        "domain:yandex.sx",
                        "domain:yandex.tj",
                        "domain:yandex.tm",
                        "domain:yandex.tr",
                        "domain:yandex.ua",
                        "domain:yandex.uz",
                        "domain:yandexadexchange.net",
                        "domain:yandexcloud.net",
                        "domain:yandexcom.net",
                        "domain:yandexmetrica.com",
                        "domain:yandexwebcache.net",
                        "domain:yandexwebcache.org",
                        "domain:yaroslavl.ru",
                        "domain:yastat.net",
                        "domain:yastatic-net.ru",
                        "domain:yastatic.net",
                        "domain:yota.ru",
                        "domain:youla-web-static.mrgcdn.ru",
                        "domain:youla.io",
                        "domain:youla.ru",
                        "domain:yuzhno-sakhalinsk.ru",
                        "domain:zdrav10.ru",
                        "domain:zentotem.net",
                        "full:api.ipify.org",
                        "full:checkip.amazonaws.com",
                        "geosite:cn",
                        "domain:cn",
                        "domain:xn--fiqs8s",
                        "domain:xn--fiqz9s",
                        "domain:xn--55qx5d",
                        "domain:xn--io0a7i",
                        "domain:ru",
                        "domain:xn--p1ai",
                        "domain:by",
                        "domain:xn--90ais",
                        "domain:ir",
                        "geosite:apple",
                        "geosite:private",
                        "geosite:apple",
                        "geosite:yandex"
                    ],
                    "outboundTag": "direct"
                },
                {
                    "ip": [
                        "geoip:cn",
                        "geoip:ru",
                        "geoip:ir"
                    ],
                    "type": "field",
                    "outboundTag": "direct"
                },
                {
                    "type": "field",
                    "inboundTag": [
                        "api",
                    ],
                    "outboundTag": "api",
                    "ruleTag": "rule-1",
                },
                {
                    "type": "field",
                    "inboundTag": [
                        "dnsQuery",
                    ],
                    "outboundTag": "proxy",
                    "ruleTag": "rule-2",
                },
                {
                    "type": "field",
                    "inboundTag": [
                        "directSocks",
                    ],
                    "outboundTag": "direct",
                    "ruleTag": "rule-3",
                },
                {
                    "type": "field",
                    "inboundTag": [
                        "api",
                    ],
                    "outboundTag": "api",
                    "ruleTag": "rule-5",
                },
                {
                    "type": "field",
                    "inboundTag": [
                        "dnsQuery",
                    ],
                    "outboundTag": "proxy",
                    "ruleTag": "rule-6",
                },
                {
                    "type": "field",
                    "inboundTag": [
                        "directSocks",
                    ],
                    "outboundTag": "direct",
                    "ruleTag": "rule-7",
                },
            ],
        },
        "policy": {
            "system": {
                "statsOutboundDownlink": True,
                "statsInboundUplink": True,
                "statsOutboundUplink": True,
                "statsInboundDownlink": True,
            },
            "levels": {
                "8": {
                    "statsUserUplink": False,
                    "handshake": 4,
                    "connIdle": 30,
                    "uplinkOnly": 1,
                    "bufferSize": 0,
                    "statsUserDownlink": False,
                    "downlinkOnly": 1,
                },
            },
        },
        "transport": {},
    }


def _client_xhttp_link_config(
    user_id: str,
    domain: str,
    public_port: int,
    path: str,
    mode: str,
    host_name: str,
) -> dict:
    link_config = _client_link_config(
        user_id,
        "unused",
        domain,
        "00",
        host_name,
    )
    link_config["remarks"] = f"Выгодный ВПН XHTTP - {host_name}"
    link_config["outbounds"] = [
        {
            "tag": "proxy",
            "protocol": "vless",
            "settings": {
                "vnext": [
                    {
                        "address": domain,
                        "port": public_port,
                        "users": [
                            {
                                "encryption": "none",
                                "id": user_id,
                                "level": 8,
                                "email": "",
                            },
                        ],
                    },
                ],
            },
            "streamSettings": {
                "network": "xhttp",
                "security": "tls",
                "tlsSettings": {
                    "serverName": domain,
                    "fingerprint": "chrome",
                },
                "xhttpSettings": {
                    "path": path,
                    "mode": mode,
                },
            },
        },
    ]
    return link_config


def _user_uuid_from_server_config(server_config: dict, user_id: str) -> str | None:
    email = f"{user_id}@example.com"
    for tag in ("xhttp", "reality-443"):
        try:
            inbound = EasyXray._inbound_by_tag(server_config, tag)
        except EasyXrayError:
            continue
        for client in inbound["settings"]["clients"]:
            if client.get("email") == email:
                return client["id"]
    return None


async def create_link(userId: str):
    """
        Создает ссылку для пользователя по конфигурации
    """
    id = None
    short_id = None
    config = load_config()
    server_config = await ConfigServer.get()
    reality = EasyXray._inbound_by_tag(server_config, "reality-443")
    clients = reality["settings"]["clients"]
    short_ids = reality["streamSettings"]["realitySettings"]["shortIds"]
    for index, client in enumerate(clients):
        if client["email"] == f"{userId}@example.com":
            id = client["id"]
            short_id = short_ids[index]
            break
    link_config = _client_link_config(
        id,
        config["Xray"]["public_key"],
        config["Xray"]["fake_site"],
        short_id,
        config["Xray"]["hostName"],
    )
    link = json.dumps(link_config, ensure_ascii=False)
    return link


async def create_xhttp_link(userId: str) -> str:
    """
    Создаёт JSON конфигурации клиента v2rayTun для VLESS XHTTP (TLS на public_port).
    """
    easy_xray = EasyXray()
    if not easy_xray._xhttp_enabled():
        raise EasyXrayError("XHTTP is disabled in config.ini ([Xhttp] enabled)")

    server_config = await ConfigServer.get()
    user_uuid = _user_uuid_from_server_config(server_config, userId)
    if not user_uuid:
        raise EasyXrayError(f"user {userId!r} not found in server config")

    xhttp_inbound = EasyXray._inbound_by_tag(server_config, "xhttp")
    xhttp_settings = xhttp_inbound["streamSettings"]["xhttpSettings"]
    path = xhttp_settings.get("path") or easy_xray._xhttp_path_from_config()
    mode = xhttp_settings.get("mode") or easy_xray._xhttp_mode()

    link_config = _client_xhttp_link_config(
        user_uuid,
        easy_xray._xhttp_domain(),
        easy_xray._xhttp_public_port(),
        path,
        mode,
        easy_xray.config["Xray"]["hostName"],
    )
    return json.dumps(link_config, ensure_ascii=False)


async def createLinkForApp(link: str):
    """
        Страница для настройки приложения
    """
    return """"
    <head>
        <meta http-equiv="refresh" content="0;URL=v2rayTun://import/{}" />
    </head>
   """.format(link)



async def suspendUser(userId: str) -> bool:
    """
        Приостонавливает пользователя в xray
    """
    try:
        subprocess.check_output(("/root/easy-xray-main/ex.sh suspend {}".format(userId)), shell=True)
        return True
    
    except subprocess.CalledProcessError as e:
        return False



async def resumeUser(userId: int):
    """
        Возобновляет доступ пользователя к xray
    """
    try:
        subprocess.check_output(("/root/easy-xray-main/ex.sh resume {}".format(userId)), shell=True)
        return True
    except subprocess.CalledProcessError as e:
        return False
    

async def suspend_users(user_ids: set[int]) -> bool:
    """
        Приостанавливает пользователей на сервере
    """
    try:

        users: str = ' '.join([str(user_id) for user_id in user_ids])

        subprocess.check_output(
            (f"/root/easy-xray-main/ex.sh suspend {users}"),
            shell=True
        )
        return True
    except Exception as e:
        return False


async def getStatistic():
    """
        Получает статистику по пользователям
        
    """

    dictRes = {}
    subprocess.check_output(("rm stats.log",), shell=True)
    os.system("/root/easy-xray-main/ex.sh stats")

    with open('stats.log') as fileLog:
        listReversFileLog = reversed(fileLog.readlines())
        for i in listReversFileLog:
            tempArrResult = i.split(' by ')
            if len(tempArrResult) > 1:
                
                arrResult = (tempArrResult[1]).split('@example.com')

                if arrResult[0] not in dictRes:
                    dictRes[arrResult[0]] = {}
                if len(arrResult) > 1:
                    dictRes[arrResult[0]][tempArrResult[0]] = arrResult[1][:-2]

        return dictRes