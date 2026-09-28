"""
rf/band_data.py - data behind the RF Band Explorer.

Frequencies are in MHz. Region keys: eu (CEPT/ETSI), na (FCC/ISED),
cn (MIIT/SRRC), jp (MIC/ARIB). Text meant for people is bilingual
({"en": ..., "ro": ...}); numbers and standard abbreviations (ERP, EIRP,
LBT, DFS, TPC, duty) are language-neutral.

This is an engineering quick reference compiled from public regulator and
standards documents; allocations and limits change and have many
sub-band exceptions. Always confirm with the current regulator text
before a compliance decision.
"""


def L(en, ro):
    return {"en": en, "ro": ro}


# ---------------------------------------------------------------------------
# Categories (id, colour, label)
# ---------------------------------------------------------------------------
CATEGORIES = [
    ("ism", "#2A9D8F", L("ISM / short-range devices", "ISM / dispozitive cu rază scurtă")),
    ("wifi", "#1D4ED8", L("Wi-Fi / WLAN", "Wi-Fi / WLAN")),
    ("wpan", "#7C3AED", L("Bluetooth / Zigbee / UWB", "Bluetooth / Zigbee / UWB")),
    ("lpwan", "#059669", L("LPWAN (LoRa, Sigfox)", "LPWAN (LoRa, Sigfox)")),
    ("rfid", "#B45309", L("RFID / NFC / wireless power", "RFID / NFC / încărcare wireless")),
    ("cell", "#DC2626", L("Cellular (2G-5G)", "Celular (2G-5G)")),
    ("gnss", "#0891B2", L("Satellite navigation (GNSS)", "Navigație prin satelit (GNSS)")),
    ("bcast", "#DB2777", L("Broadcast (radio / TV)", "Radiodifuziune (radio / TV)")),
    ("ham", "#65A30D", L("Amateur / personal radio", "Radioamatori / radio personal")),
    ("nav", "#475569", L("Aviation / maritime", "Aviație / maritim")),
    ("sat", "#9333EA", L("Satellite / radar / mmWave", "Satelit / radar / unde milimetrice")),
]
CAT_COLOR = {c[0]: c[1] for c in CATEGORIES}

REGIONS = [("eu", L("Europe (CEPT/ETSI)", "Europa (CEPT/ETSI)")),
           ("na", L("North America (FCC/ISED)", "America de Nord (FCC/ISED)")),
           ("cn", L("China (MIIT/SRRC)", "China (MIIT/SRRC)")),
           ("jp", L("Japan (MIC/ARIB)", "Japonia (MIC/ARIB)"))]


# ---------------------------------------------------------------------------
# Channel generators: return [(centre MHz, width MHz, label), ...]
# ---------------------------------------------------------------------------
def _wifi24():
    ch = [(2407 + 5 * n, 20, str(n)) for n in range(1, 14)]
    return ch + [(2484, 22, "14")]


def _wifi5():
    out = []
    for n in list(range(36, 65, 4)) + list(range(100, 145, 4)) + list(range(149, 178, 4)):
        out.append((5000 + 5 * n, 20, str(n)))
    return out


def _wifi6():
    return [(5950 + 5 * n, 20, str(n)) for n in range(1, 234, 4)]


def _bt():
    return [(2402 + k, 1, str(k)) for k in range(79)]


def _ble():
    # RF channel k at 2402 + 2k MHz; advertising channels 37/38/39 are RF 0, 12, 39
    names = {}
    data = 0
    for k in range(40):
        if k == 0:
            names[k] = "37"
        elif k == 12:
            names[k] = "38"
        elif k == 39:
            names[k] = "39"
        else:
            names[k] = str(data)
            data += 1
    return [(2402 + 2 * k, 2, names[k]) for k in range(40)]


def _zigbee():
    return [(2405 + 5 * (k - 11), 2, str(k)) for k in range(11, 27)]


def _lora_eu():
    return [(868.1, 0.125, "868.1"), (868.3, 0.125, "868.3"), (868.5, 0.125, "868.5"),
            (867.1, 0.125, "867.1"), (867.3, 0.125, "867.3"), (867.5, 0.125, "867.5"),
            (867.7, 0.125, "867.7"), (867.9, 0.125, "867.9"), (869.525, 0.125, "RX2")]


def _lora_us():
    ch = [(902.3 + 0.2 * n, 0.125, str(n)) for n in range(64)]
    ch += [(903.0 + 1.6 * n, 0.5, str(64 + n)) for n in range(8)]
    ch += [(923.3 + 0.6 * n, 0.5, "D" + str(n)) for n in range(8)]
    return ch


def _gsm900():
    # uplink carriers of P-GSM, ARFCN 1..124, plus the downlink 45 MHz above
    return [(890 + 0.2 * n, 0.2, str(n)) for n in range(1, 125)] + \
           [(935 + 0.2 * n, 0.2, str(n)) for n in range(1, 125)]


def _fm():
    return [(87.6 + 0.2 * n, 0.2, "") for n in range(103)]


def _dvbt():
    return [(306 + 8 * n, 8, str(n)) for n in range(21, 49)]


def _dect():
    return [(1897.344 - 1.728 * n, 1.728, str(n)) for n in range(10)]


def _pmr446():
    return [(446.00625 + 0.0125 * (n - 1), 0.0125, str(n)) for n in range(1, 17)]


def _cb():
    f = [26.965, 26.975, 26.985, 27.005, 27.015, 27.025, 27.035, 27.055, 27.065, 27.075,
         27.085, 27.105, 27.115, 27.125, 27.135, 27.155, 27.165, 27.175, 27.185, 27.205,
         27.215, 27.225, 27.255, 27.235, 27.245, 27.265, 27.275, 27.285, 27.295, 27.305,
         27.315, 27.325, 27.335, 27.345, 27.355, 27.365, 27.375, 27.385, 27.395, 27.405]
    return [(x, 0.01, str(i + 1)) for i, x in enumerate(f)]


def _rfid_eu():
    return [(865.7, 0.2, "4"), (866.3, 0.2, "7"), (866.9, 0.2, "10"), (867.5, 0.2, "13")]


def _rfid_us():
    return [(902.75 + 0.5 * n, 0.5, str(n)) for n in range(50)]


def _wigig():
    return [(56160 + 2160 * n, 2160, str(n)) for n in range(1, 7)]


def _uwb():
    return [(3494.4 + 499.2 * (n - 1), 499.2, str(n)) for n in (1, 2, 3)] + \
           [(6489.6, 499.2, "5"), (6988.8, 499.2, "6"), (7987.2, 499.2, "9"), (8486.4, 499.2, "10")]


def _marine():
    out = [(156.050 + 0.05 * (n - 1), 0.025, str(n)) for n in range(1, 29)]
    out.append((156.800, 0.025, "16"))
    return out


def _nr_n78():
    return [(3300 + 100 * k + 50, 100, "") for k in range(5)]


# ---------------------------------------------------------------------------
# Allocations
#   lo, hi   : envelope (MHz) used by the spectrum ruler and the lookup
#   ranges   : per region text
#   power    : per region max power text
#   access   : per region access rules (duty cycle / LBT / DFS / licence)
#   chan     : channel plan (count, spacing, width, centre formula)
#   plot     : (generator, span lo, span hi) for the channel diagram
# ---------------------------------------------------------------------------
BANDS = [
    # ---------------- ISM / SRD ----------------
    dict(id="ism433", cat="ism", lo=433.05, hi=434.79,
         name=L("433 MHz ISM / SRD", "ISM / SRD 433 MHz"),
         ranges=dict(eu="433.05-434.79 MHz", na="Not ISM (Part 15.231 periodic TX, 260-470 MHz)",
                     cn="433.00-434.79 MHz", jp="Not for general SRD (433.67-434.17 active RFID only)"),
         power=dict(eu="10 mW ERP (1 mW/10 kHz wideband)", na="Field-strength limit (~ -20 dBm EIRP)",
                    cn="10 mW ERP", jp="-"),
         access=dict(eu="10 % duty (sub-band dependent)", na="Periodic / event TX only",
                     cn="Micro-power device rules", jp="-"),
         chan=dict(count="Free (typ. 433.92 MHz centre)", spacing="25 kHz typical", width="≤ 25 kHz narrowband or wideband",
                   formula="Centre 433.92 MHz (ITU-R Region 1 ISM)"),
         tech="OOK/ASK, FSK remotes, weather stations, car keys (EU), LoRa EU433",
         notes=L("ISM band only in ITU Region 1 (Europe/Africa). Very crowded: key fobs, garage doors, sensors. "
                 "Antenna λ/4 ≈ 17.3 cm. In North America the same frequencies are used under different, "
                 "much stricter periodic-transmission rules (FCC 15.231).",
                 "Bandă ISM doar în Regiunea 1 ITU (Europa/Africa). Foarte aglomerată: telecomenzi, porți de garaj, "
                 "senzori. Antenă λ/4 ≈ 17,3 cm. În America de Nord aceleași frecvențe se folosesc cu reguli "
                 "mult mai stricte de transmisie periodică (FCC 15.231).")),
    dict(id="srd868", cat="ism", lo=863, hi=870,
         name=L("868 MHz SRD (Europe) / 915 MHz ISM", "SRD 868 MHz (Europa) / ISM 915 MHz"),
         ranges=dict(eu="863-870 MHz (ERC Rec 70-03 sub-bands)", na="902-928 MHz ISM",
                     cn="470-510 MHz (metering), 779-787 MHz", jp="920.5-928.1 MHz (ARIB STD-T108)"),
         power=dict(eu="25 mW ERP (500 mW in 869.4-869.65)", na="1 W conducted + 6 dBi (15.247)",
                    cn="50 mW (470-510), 10 mW (779-787)", jp="20 mW (250 mW registered)"),
         access=dict(eu="0.1 %-10 % duty or LBT+AFA per sub-band", na="FHSS ≥ 50 ch or digital modulation",
                     cn="Duty-cycle limits", jp="LBT (carrier sense), TX time limits"),
         chan=dict(count="Sub-bands g, g1-g4 (EU)", spacing="25-200 kHz typical", width="≤ 600 kHz",
                   formula="EU: 868.0-868.6 (1 %), 868.7-869.2 (0.1 %), 869.4-869.65 (10 %, 500 mW), 869.7-870 (5 mW)"),
         tech="Sensors, alarms, smart meters, Z-Wave (868.42 / 908.42 MHz), Wireless M-Bus, LoRa, Sigfox",
         notes=L("Sub-GHz propagates much better than 2.4 GHz (≈ 9 dB less free-space loss and better wall "
                 "penetration) at the price of low data rates and strict duty-cycle rules. The same radio chip "
                 "usually needs a different band plan per region: 868 MHz in Europe, 915 MHz in the Americas, "
                 "920 MHz in Japan, 470 or 779 MHz in China.",
                 "Sub-GHz se propagă mult mai bine decât 2,4 GHz (≈ 9 dB pierderi mai mici în spațiu liber și "
                 "pătrundere mai bună prin pereți), cu prețul unor debite mici și al unor reguli stricte de ciclu "
                 "de lucru. Același cip radio are de obicei nevoie de alt plan de benzi în fiecare regiune: 868 MHz "
                 "în Europa, 915 MHz în America, 920 MHz în Japonia, 470 sau 779 MHz în China.")),
    dict(id="ism24", cat="ism", lo=2400, hi=2483.5,
         name=L("2.4 GHz ISM (worldwide)", "ISM 2,4 GHz (mondial)"),
         ranges=dict(eu="2400-2483.5 MHz", na="2400-2483.5 MHz", cn="2400-2483.5 MHz", jp="2400-2483.5 MHz"),
         power=dict(eu="100 mW EIRP (EN 300 328)", na="1 W conducted, 4 W EIRP", cn="100 mW EIRP",
                    jp="10 mW/MHz (ARIB STD-T66)"),
         access=dict(eu="LBT or adaptivity for > 10 dBm", na="FHSS or digital modulation", cn="-", jp="-"),
         chan=dict(count="Shared by Wi-Fi, Bluetooth, Zigbee, microwave ovens", spacing="-", width="83.5 MHz total",
                   formula="Centre 2450 MHz"),
         tech="Wi-Fi b/g/n/ax, Bluetooth, BLE, Zigbee/Thread, proprietary, microwave ovens (≈ 2.45 GHz)",
         notes=L("The only license-free band available everywhere in the world, which is why it is so crowded. "
                 "Microwave ovens heat water at ≈ 2.45 GHz and leak interference into the upper Wi-Fi channels.",
                 "Singura bandă fără licență disponibilă peste tot în lume, de aceea este atât de aglomerată. "
                 "Cuptoarele cu microunde încălzesc apa la ≈ 2,45 GHz și produc interferențe pe canalele Wi-Fi superioare.")),
    dict(id="ism24g", cat="ism", lo=24000, hi=24250,
         name=L("24 GHz ISM (radar sensors)", "ISM 24 GHz (senzori radar)"),
         ranges=dict(eu="24.00-24.25 GHz", na="24.00-24.25 GHz", cn="24.00-24.25 GHz", jp="24.05-24.25 GHz"),
         power=dict(eu="100 mW EIRP", na="Field strength 2.5 V/m @ 3 m (15.249)", cn="20 mW EIRP", jp="20 mW"),
         access=dict(eu="-", na="-", cn="-", jp="-"),
         chan=dict(count="1 (250 MHz)", spacing="-", width="250 MHz", formula="Centre 24.125 GHz"),
         tech="Doppler motion sensors, FMCW level/distance radar, door openers",
         notes=L("Cheap K-band radar modules (e.g. 24.125 GHz Doppler) live here. The 250 MHz width limits FMCW "
                 "range resolution to ΔR = c/(2B) ≈ 0.6 m.",
                 "Aici lucrează modulele radar ieftine în banda K (ex. Doppler 24,125 GHz). Lățimea de 250 MHz "
                 "limitează rezoluția în distanță FMCW la ΔR = c/(2B) ≈ 0,6 m.")),

    # ---------------- Wi-Fi ----------------
    dict(id="wifi24", cat="wifi", lo=2401, hi=2495,
         name=L("Wi-Fi 2.4 GHz (802.11b/g/n/ax)", "Wi-Fi 2,4 GHz (802.11b/g/n/ax)"),
         ranges=dict(eu="Ch 1-13 (2412-2472 MHz)", na="Ch 1-11 (2412-2462 MHz)", cn="Ch 1-13",
                     jp="Ch 1-13, ch 14 (2484 MHz, 802.11b only)"),
         power=dict(eu="100 mW EIRP", na="1 W conducted (+6 dBi)", cn="100 mW EIRP", jp="10 mW/MHz"),
         access=dict(eu="Adaptivity (LBT)", na="-", cn="-", jp="-"),
         chan=dict(count="13 (+ ch 14 in Japan)", spacing="5 MHz", width="20 MHz (22 MHz DSSS), 40 MHz optional",
                   formula="f = 2407 + 5·n MHz (n = 1…13); ch 14 = 2484 MHz"),
         plot=(_wifi24, 2395, 2500),
         tech="OFDM up to 1024-QAM (Wi-Fi 6), DSSS/CCK for 802.11b",
         notes=L("Channels are only 5 MHz apart but 20 MHz wide, so neighbours overlap. Use 1/6/11 in North "
                 "America or 1/5/9/13 in Europe for non-overlapping 20 MHz networks. 40 MHz channels are "
                 "rarely a good idea at 2.4 GHz.",
                 "Canalele sunt la doar 5 MHz unul de altul dar au 20 MHz lățime, deci se suprapun. Folosește "
                 "1/6/11 în America de Nord sau 1/5/9/13 în Europa pentru rețele de 20 MHz fără suprapunere. "
                 "Canalele de 40 MHz sunt rareori o idee bună la 2,4 GHz.")),
    dict(id="wifi5", cat="wifi", lo=5150, hi=5895,
         name=L("Wi-Fi 5 GHz (802.11a/n/ac/ax)", "Wi-Fi 5 GHz (802.11a/n/ac/ax)"),
         ranges=dict(eu="5150-5350, 5470-5725 MHz (5725-5850 SRD, 25 mW)",
                     na="5150-5350, 5470-5725, 5725-5895 MHz (U-NII-1…4)",
                     cn="5150-5350, 5725-5850 MHz", jp="W52 5150-5250, W53 5250-5350, W56 5470-5730 MHz"),
         power=dict(eu="200 mW EIRP (5150-5350, indoor), 1 W EIRP (5470-5725)",
                    na="U-NII-1: 1 W conducted; U-NII-2A/2C: 250 mW; U-NII-3: 1 W",
                    cn="200 mW (5.2 GHz indoor), ≤ 33 dBm EIRP (5.8 GHz)", jp="200 mW EIRP (W52/W53), 1 W (W56)"),
         access=dict(eu="DFS + TPC above 5250 MHz", na="DFS on U-NII-2A/2C", cn="DFS on 5250-5350",
                     jp="DFS on W53/W56; W52 indoor"),
         chan=dict(count="Up to 25 × 20 MHz, 12 × 40, 6 × 80, 2-3 × 160 MHz", spacing="20 MHz",
                   width="20 / 40 / 80 / 160 MHz", formula="f = 5000 + 5·n MHz (n = 36, 40 … 177)"),
         plot=(_wifi5, 5140, 5900),
         tech="OFDM, MU-MIMO, OFDMA (Wi-Fi 6)",
         notes=L("DFS (dynamic frequency selection) means the access point must listen for weather and military "
                 "radars and vacate the channel if one is detected — this is why some 5 GHz channels take 1-10 "
                 "minutes to come up. Channel 144 and U-NII-4 (149-177 extension) are not available everywhere.",
                 "DFS (selecție dinamică a frecvenței) înseamnă că punctul de acces trebuie să asculte radarele "
                 "meteo și militare și să elibereze canalul dacă detectează unul — de aceea unele canale de 5 GHz "
                 "pornesc abia după 1-10 minute. Canalul 144 și U-NII-4 (extensia 149-177) nu sunt disponibile peste tot.")),
    dict(id="wifi6", cat="wifi", lo=5925, hi=7125,
         name=L("Wi-Fi 6 GHz (6E / Wi-Fi 7)", "Wi-Fi 6 GHz (6E / Wi-Fi 7)"),
         ranges=dict(eu="5945-6425 MHz (lower 6 GHz)", na="5925-7125 MHz (1200 MHz)",
                     cn="Not for Wi-Fi (6425-7125 MHz assigned to IMT/5G)", jp="5925-6425 MHz"),
         power=dict(eu="LPI 23 dBm EIRP (10 dBm/MHz); VLP 14 dBm", na="LPI 5 dBm/MHz (≤ 30 dBm AP); SP with AFC up to 36 dBm",
                    cn="-", jp="LPI 23 dBm EIRP; VLP 14 dBm"),
         access=dict(eu="Indoor (LPI) or very-low-power portable", na="LPI indoor; standard power needs AFC database",
                     cn="-", jp="Indoor / VLP"),
         chan=dict(count="59 × 20, 29 × 40, 14 × 80, 7 × 160, 3 × 320 MHz (US)", spacing="20 MHz",
                   width="20 … 320 MHz", formula="f = 5950 + 5·n MHz (n = 1, 5 … 233)"),
         plot=(_wifi6, 5920, 7130),
         tech="Wi-Fi 6E (802.11ax), Wi-Fi 7 (802.11be, 320 MHz, 4096-QAM, MLO)",
         notes=L("A clean band with no legacy devices; 6 GHz clients must support WPA3. Europe opened only the "
                 "lower 480 MHz so far; China reserved the upper part for 5G.",
                 "O bandă curată, fără dispozitive vechi; clienții de 6 GHz trebuie să suporte WPA3. Europa a "
                 "deschis până acum doar partea inferioară de 480 MHz; China a rezervat partea superioară pentru 5G.")),
    dict(id="wigig", cat="wifi", lo=57000, hi=71000,
         name=L("60 GHz WiGig (802.11ad/ay)", "WiGig 60 GHz (802.11ad/ay)"),
         ranges=dict(eu="57-71 GHz", na="57-71 GHz", cn="59-64 GHz (+ 45 GHz for 802.11aj)", jp="57-66 GHz"),
         power=dict(eu="40 dBm EIRP", na="40 dBm EIRP avg (43 dBm peak)", cn="-", jp="10 dBm + up to 47 dBi antenna"),
         access=dict(eu="-", na="-", cn="-", jp="-"),
         chan=dict(count="6", spacing="2160 MHz", width="2160 MHz (bonding up to 8.64 GHz)",
                   formula="f = 56.16 + 2.16·n GHz (n = 1…6)"),
         plot=(_wigig, 56000, 72000),
         tech="Single-carrier/OFDM, beamforming phased arrays, multi-Gbit/s",
         notes=L("Oxygen absorbs about 15 dB/km at 60 GHz and walls block it almost completely, so links are "
                 "short and naturally secure; very wide channels give multi-gigabit rates.",
                 "Oxigenul absoarbe aproximativ 15 dB/km la 60 GHz, iar pereții îl blochează aproape complet, "
                 "deci legăturile sunt scurte și natural securizate; canalele foarte largi dau debite de mai mulți Gbit/s.")),

    # ---------------- WPAN ----------------
    dict(id="bt", cat="wpan", lo=2400, hi=2483.5,
         name=L("Bluetooth Classic (BR/EDR)", "Bluetooth Clasic (BR/EDR)"),
         ranges=dict(eu="2402-2480 MHz", na="2402-2480 MHz", cn="2402-2480 MHz", jp="2402-2480 MHz"),
         power=dict(eu="Class 1: 100 mW, Class 2: 2.5 mW, Class 3: 1 mW", na="same classes", cn="same classes",
                    jp="same classes"),
         access=dict(eu="FHSS 1600 hops/s, AFH", na="FHSS", cn="FHSS", jp="FHSS"),
         chan=dict(count="79", spacing="1 MHz", width="1 MHz", formula="f = 2402 + k MHz (k = 0…78)"),
         plot=(_bt, 2398, 2484),
         tech="GFSK 1 Mbit/s, π/4-DQPSK 2 Mbit/s, 8DPSK 3 Mbit/s (EDR)",
         notes=L("Adaptive frequency hopping (AFH) marks channels occupied by Wi-Fi as bad and skips them.",
                 "Salturile de frecvență adaptive (AFH) marchează canalele ocupate de Wi-Fi ca proaste și le evită.")),
    dict(id="ble", cat="wpan", lo=2400, hi=2483.5,
         name=L("Bluetooth Low Energy (BLE)", "Bluetooth Low Energy (BLE)"),
         ranges=dict(eu="2402-2480 MHz", na="2402-2480 MHz", cn="2402-2480 MHz", jp="2402-2480 MHz"),
         power=dict(eu="≤ 100 mW (typ. 1-10 mW)", na="≤ 100 mW", cn="≤ 100 mW", jp="≤ 10 mW/MHz"),
         access=dict(eu="Channel hopping", na="-", cn="-", jp="-"),
         chan=dict(count="40 (37 data + 3 advertising)", spacing="2 MHz", width="2 MHz",
                   formula="f = 2402 + 2·k MHz (k = 0…39); advertising 37/38/39 = 2402/2426/2480 MHz"),
         plot=(_ble, 2398, 2484),
         tech="GFSK 1 or 2 Mbit/s, Coded PHY (S=2/S=8) for long range, direction finding (AoA/AoD)",
         notes=L("The three advertising channels were placed in the gaps between Wi-Fi channels 1, 6 and 11 "
                 "so devices can always be discovered.",
                 "Cele trei canale de anunț au fost plasate în golurile dintre canalele Wi-Fi 1, 6 și 11, "
                 "astfel încât dispozitivele să poată fi descoperite mereu.")),
    dict(id="zigbee", cat="wpan", lo=2400, hi=2483.5,
         name=L("Zigbee / Thread / 802.15.4", "Zigbee / Thread / 802.15.4"),
         ranges=dict(eu="2405-2480 MHz; 868.3 MHz (ch 0)", na="2405-2480 MHz; 906-924 MHz (ch 1-10)",
                     cn="2405-2480 MHz; 779-787 MHz", jp="2405-2480 MHz; 920 MHz"),
         power=dict(eu="100 mW EIRP", na="1 W", cn="100 mW", jp="10 mW/MHz"),
         access=dict(eu="-", na="-", cn="-", jp="-"),
         chan=dict(count="16 at 2.4 GHz (ch 11-26)", spacing="5 MHz", width="2 MHz",
                   formula="f = 2405 + 5·(k − 11) MHz (k = 11…26)"),
         plot=(_zigbee, 2398, 2484),
         tech="O-QPSK DSSS 250 kbit/s (2.4 GHz), BPSK 20/40 kbit/s (sub-GHz)",
         notes=L("Channels 15, 20, 25 and 26 fall between the usual Wi-Fi channels 1/6/11 and are the best "
                 "choice in homes with Wi-Fi.",
                 "Canalele 15, 20, 25 și 26 cad între canalele Wi-Fi uzuale 1/6/11 și sunt cea mai bună "
                 "alegere în locuințele cu Wi-Fi.")),
    dict(id="uwb", cat="wpan", lo=3100, hi=10600,
         name=L("Ultra-wideband (UWB, 802.15.4z)", "Bandă ultra-largă (UWB, 802.15.4z)"),
         ranges=dict(eu="6.0-8.5 GHz (3.1-4.8 GHz with mitigation)", na="3.1-10.6 GHz",
                     cn="≈ 7.2-8.8 GHz (MIIT 2024 rules, verify)", jp="3.4-4.8 GHz, 7.25-10.25 GHz"),
         power=dict(eu="-41.3 dBm/MHz EIRP", na="-41.3 dBm/MHz EIRP", cn="-41.3 dBm/MHz", jp="-41.3 dBm/MHz"),
         access=dict(eu="Low duty / mitigation outside 6-8.5 GHz", na="-", cn="Indoor-oriented", jp="-"),
         chan=dict(count="16 HRP channels (ch 0-15)", spacing="499.2 MHz", width="499.2 MHz (up to 1.33 GHz)",
                   formula="ch 5 = 6489.6 MHz, ch 9 = 7987.2 MHz (most used)"),
         plot=(_uwb, 3000, 9000),
         tech="Impulse radio, ~2 ns pulses, time-of-flight ranging to ±10 cm (FiRa, CCC digital car key, AirTag)",
         notes=L("The power density is so low (below the unintentional-emission limit) that UWB is almost "
                 "invisible to other services; it wins by its enormous bandwidth, which gives precise timing.",
                 "Densitatea de putere este atât de mică (sub limita emisiilor neintenționate) încât UWB este aproape "
                 "invizibil pentru alte servicii; câștigul vine din lățimea de bandă enormă, care dă o măsurare "
                 "precisă a timpului.")),
    dict(id="dect", cat="wpan", lo=1880, hi=1930,
         name=L("DECT cordless phones", "Telefoane fără fir DECT"),
         ranges=dict(eu="1880-1900 MHz", na="1920-1930 MHz (DECT 6.0)", cn="-", jp="1893.5-1906.1 MHz (J-DECT)"),
         power=dict(eu="250 mW peak", na="~ 100 mW", cn="-", jp="-"),
         access=dict(eu="TDMA, 24 slots/frame, dynamic channel selection", na="LBT", cn="-", jp="Carrier sense"),
         chan=dict(count="10 (EU), 5 (US)", spacing="1.728 MHz", width="1.728 MHz",
                   formula="EU: f = 1897.344 − 1.728·n MHz (n = 0…9)"),
         plot=(_dect, 1878, 1900),
         tech="GFSK, TDMA/TDD 10 ms frames; DECT NR+ (DECT-2020) for IoT mesh",
         notes=L("A dedicated band means DECT phones do not suffer from Wi-Fi interference.",
                 "Banda dedicată face ca telefoanele DECT să nu fie deranjate de Wi-Fi.")),

    # ---------------- LPWAN ----------------
    dict(id="lora", cat="lpwan", lo=863, hi=928,
         name=L("LoRaWAN regional plans", "Planuri regionale LoRaWAN"),
         ranges=dict(eu="EU868: 863-870 MHz (EU433 also)", na="US915: 902-928 MHz",
                     cn="CN470: 470-510 MHz", jp="AS923-1: 920-923.4 MHz"),
         power=dict(eu="14 dBm ERP (27 dBm on 869.525)", na="30 dBm conducted", cn="19.15 dBm EIRP", jp="16 dBm EIRP"),
         access=dict(eu="1 % duty (10 % on 869.4-869.65)", na="400 ms dwell time, hopping", cn="-",
                     jp="LBT, 400 ms dwell"),
         chan=dict(count="EU: 3 default + 5 extra; US: 64 × 125 kHz + 8 × 500 kHz up, 8 down",
                   spacing="200 kHz (EU/US 125 kHz ch)", width="125 / 250 / 500 kHz",
                   formula="US up: 902.3 + 0.2·n MHz (n = 0…63); US down: 923.3 + 0.6·n MHz; "
                           "CN up: 470.3 + 0.2·n (n = 0…95)"),
         plot=(_lora_eu, 866.8, 869.8),
         tech="Chirp spread spectrum, SF7-SF12, 0.3-50 kbit/s, −137 dBm sensitivity at SF12/125 kHz",
         notes=L("Spreading factor trades speed for range: each step up (SF7 → SF12) roughly doubles airtime "
                 "and gains 2.5 dB. With 1 % duty cycle in Europe an SF12 51-byte packet (~2.5 s airtime) "
                 "allows only about one message every 4 minutes. China restricted 470-510 MHz to metering "
                 "use in newer MIIT rules — check before deploying.",
                 "Factorul de împrăștiere schimbă viteza pe distanță: fiecare treaptă (SF7 → SF12) aproape "
                 "dublează timpul în aer și câștigă 2,5 dB. Cu ciclul de lucru de 1 % din Europa, un pachet "
                 "SF12 de 51 de octeți (~2,5 s în aer) permite doar un mesaj la circa 4 minute. China a "
                 "restricționat 470-510 MHz la contorizare în regulile MIIT mai noi — verifică înainte de implementare.")),
    dict(id="sigfox", cat="lpwan", lo=868.034, hi=868.226,
         name=L("Sigfox (ultra-narrowband)", "Sigfox (bandă ultra-îngustă)"),
         ranges=dict(eu="RC1: 868.034-868.226 MHz", na="RC2/RC4: 902.1-905.2 MHz", cn="-",
                     jp="RC3: 923.2 MHz"),
         power=dict(eu="14 dBm ERP", na="22-24 dBm", cn="-", jp="16 dBm"),
         access=dict(eu="1 % duty → 140 msgs/day", na="FHSS/hybrid", cn="-", jp="LBT"),
         chan=dict(count="Random frequency in a 192 kHz window", spacing="-", width="100 Hz (EU) / 600 Hz (US)",
                   formula="Centre 868.130 MHz (RC1)"),
         tech="DBPSK 100 bit/s uplink, 12-byte payload, 3 repetitions on random frequencies",
         notes=L("Extremely narrow signals put all the energy into 100 Hz, so the receiver noise floor is only "
                 "about −154 dBm — the trick behind its long range.",
                 "Semnalele extrem de înguste concentrează toată energia în 100 Hz, deci zgomotul receptorului "
                 "este doar de circa −154 dBm — acesta e secretul distanței mari.")),

    # ---------------- RFID / NFC / WPT ----------------
    dict(id="lfrfid", cat="rfid", lo=0.119, hi=0.135,
         name=L("LF RFID 125 / 134.2 kHz", "RFID LF 125 / 134,2 kHz"),
         ranges=dict(eu="119-135 kHz", na="119-135 kHz", cn="119-135 kHz", jp="119-135 kHz"),
         power=dict(eu="H-field 66 dBµA/m @ 10 m", na="Part 15.209", cn="-", jp="-"),
         access=dict(eu="-", na="-", cn="-", jp="-"),
         chan=dict(count="1", spacing="-", width="few kHz", formula="125 kHz (access cards), 134.2 kHz (animal ID ISO 11784/5)"),
         tech="Inductive coupling, ASK/FSK, EM4100, HID Prox, pet microchips, car immobilisers",
         notes=L("Works through water and tissue, so it is used for animal implants; range is a few cm to ~1 m.",
                 "Trece prin apă și țesut, de aceea se folosește la implanturile pentru animale; distanța este de "
                 "câțiva cm până la ~1 m.")),
    dict(id="nfc", cat="rfid", lo=13.553, hi=13.567,
         name=L("NFC / HF RFID 13.56 MHz", "NFC / RFID HF 13,56 MHz"),
         ranges=dict(eu="13.553-13.567 MHz", na="13.553-13.567 MHz", cn="13.553-13.567 MHz", jp="13.553-13.567 MHz"),
         power=dict(eu="42 dBµA/m @ 10 m", na="15.225: 15.848 mV/m @ 30 m", cn="-", jp="-"),
         access=dict(eu="-", na="-", cn="-", jp="-"),
         chan=dict(count="1", spacing="-", width="±7 kHz (sidebands at ±847.5 kHz allowed at lower level)",
                   formula="fc = 13.56 MHz; subcarrier fc/16 = 847.5 kHz"),
         tech="ISO 14443 A/B (payments, passports), ISO 15693 (vicinity), FeliCa; 106-848 kbit/s",
         notes=L("Near-field magnetic coupling: the reader coil and the tag coil form a loosely coupled "
                 "transformer (see the inductor coupling tab). Range < 10 cm by design.",
                 "Cuplaj magnetic în câmp apropiat: bobina cititorului și cea a etichetei formează un transformator "
                 "slab cuplat (vezi fila de cuplaj al bobinelor). Distanță < 10 cm prin proiectare.")),
    dict(id="uhfrfid", cat="rfid", lo=860, hi=960,
         name=L("UHF RFID (EPC Gen2)", "RFID UHF (EPC Gen2)"),
         ranges=dict(eu="865.6-867.6 MHz (+ 915-921 MHz)", na="902-928 MHz", cn="920.5-924.5 MHz (+ 840.5-844.5)",
                     jp="916.7-920.9 MHz"),
         power=dict(eu="2 W ERP (4 W ERP at 915-921)", na="4 W EIRP", cn="2 W ERP", jp="4 W EIRP (registered)"),
         access=dict(eu="4 high-power channels, LBT not required", na="FHSS 50 ch", cn="FHSS 16 ch", jp="LBT or registered"),
         chan=dict(count="EU 4, US 50, CN 16", spacing="EU 600 kHz, US 500 kHz, CN 250 kHz", width="200-500 kHz",
                   formula="EU: 864.9 + 0.2·n MHz (n = 4, 7, 10, 13)"),
         plot=(_rfid_us, 901, 929),
         tech="Passive backscatter, PIE/ASK reader, FM0/Miller tag, reads up to ~10 m",
         notes=L("A tag must work in every region, so tag antennas are tuned for 860-960 MHz; readers are "
                 "region-specific.",
                 "O etichetă trebuie să funcționeze în orice regiune, deci antenele etichetelor sunt acordate pe "
                 "860-960 MHz; cititoarele sunt specifice fiecărei regiuni.")),
    dict(id="qi", cat="rfid", lo=0.087, hi=0.205,
         name=L("Qi wireless charging", "Încărcare wireless Qi"),
         ranges=dict(eu="87-205 kHz", na="87-205 kHz", cn="100-148.5 kHz (WPT rules)", jp="110-205 kHz"),
         power=dict(eu="Up to 15 W (BPP 5 W), Qi2 15-25 W", na="same", cn="same", jp="same"),
         access=dict(eu="-", na="-", cn="-", jp="-"),
         chan=dict(count="1 (variable frequency control)", spacing="-", width="-", formula="Power set by frequency / duty"),
         tech="Resonant inductive coupling, in-band ASK/FSK communication",
         notes=L("Transformer with an air gap: the coupling factor is only about 0.3-0.7, so coil alignment "
                 "(Qi2 uses magnets) matters a lot for efficiency.",
                 "Transformator cu întrefier: factorul de cuplaj este doar de circa 0,3-0,7, deci alinierea "
                 "bobinelor (Qi2 folosește magneți) contează mult pentru randament.")),

    # ---------------- Cellular ----------------
    dict(id="gsm", cat="cell", lo=824, hi=1990,
         name=L("2G GSM (legacy)", "2G GSM (moștenire)"),
         ranges=dict(eu="GSM900 (880-915 / 925-960), DCS1800 (1710-1785 / 1805-1880)",
                     na="GSM850 (824-849 / 869-894), PCS1900 (1850-1910 / 1930-1990)",
                     cn="GSM900, DCS1800", jp="Never deployed (Japan used PDC, closed 2012)"),
         power=dict(eu="Handset 2 W (900) / 1 W (1800) peak", na="same", cn="same", jp="-"),
         access=dict(eu="Licensed", na="Licensed; mostly shut down", cn="Licensed; being phased out", jp="-"),
         chan=dict(count="124 (P-GSM), 374 (DCS1800)", spacing="200 kHz", width="200 kHz, 8 TDMA slots",
                   formula="GSM900 UL = 890 + 0.2·n MHz, DL = UL + 45 MHz (ARFCN n = 1…124)"),
         plot=(_gsm900, 885, 965),
         tech="GMSK 270.833 kbit/s, TDMA 8 slots, FDD",
         notes=L("FDD: every carrier is a pair — uplink (phone → tower) and downlink 45 MHz higher at 900 MHz "
                 "(95 MHz at 1800). North American operators have switched 2G off; Japan never used GSM at all.",
                 "FDD: fiecare purtătoare este o pereche — legătura ascendentă (telefon → antenă) și cea "
                 "descendentă cu 45 MHz mai sus la 900 MHz (95 MHz la 1800). Operatorii din America de Nord au "
                 "oprit 2G; Japonia nu a folosit niciodată GSM.")),
    dict(id="lte_low", cat="cell", lo=617, hi=960,
         name=L("LTE / NR low bands (< 1 GHz)", "LTE / NR benzi joase (< 1 GHz)"),
         ranges=dict(eu="B20 (832-862 / 791-821), B8 (880-915 / 925-960), B28 (703-733 / 758-788)",
                     na="B71 (663-698 / 617-652), B12 (699-716 / 729-746), B13, B14, B5 (824-849 / 869-894)",
                     cn="B5, B8, B28 (n28)", jp="B18/B26 (815-830 / 860-875), B19, B28, B8 (partial)"),
         power=dict(eu="UE 23 dBm (Power class 3)", na="UE 23 dBm", cn="UE 23 dBm", jp="UE 23 dBm"),
         access=dict(eu="Licensed", na="Licensed", cn="Licensed", jp="Licensed"),
         chan=dict(count="Carrier bandwidths 1.4 / 3 / 5 / 10 / 15 / 20 MHz", spacing="100 kHz raster",
                   width="up to 20 MHz (LTE)", formula="F_DL = F_DL,low + 0.1·(N_DL − N_Offs) MHz (EARFCN)"),
         tech="OFDMA downlink, SC-FDMA uplink, 15 kHz subcarriers",
         notes=L("Low bands give coverage (rural areas, deep indoor); B20 is the classic European rural LTE band. "
                 "Band numbers are 3GPP-wide, but each country licenses only some of them.",
                 "Benzile joase dau acoperire (zone rurale, interior adânc); B20 este banda LTE rurală clasică "
                 "din Europa. Numerele benzilor sunt comune 3GPP, dar fiecare țară licențiază doar o parte din ele.")),
    dict(id="lte_mid", cat="cell", lo=1427, hi=2690,
         name=L("LTE / NR mid bands (1.4-2.7 GHz)", "LTE / NR benzi medii (1,4-2,7 GHz)"),
         ranges=dict(eu="B3 (1710-1785 / 1805-1880), B1 (1920-1980 / 2110-2170), B7 (2500-2570 / 2620-2690), B32 SDL",
                     na="B2/n2 PCS, B66 (1710-1780 / 2110-2200), B41/n41 TDD 2496-2690",
                     cn="B1, B3, B34/B39 TDD, B40 TDD 2300-2400, B41 TDD", jp="B1, B3, B11/B21 (1.5 GHz), B41"),
         power=dict(eu="UE 23 dBm", na="UE 23 dBm (26 dBm HPUE on n41)", cn="UE 23 dBm", jp="UE 23 dBm"),
         access=dict(eu="Licensed", na="Licensed", cn="Licensed", jp="Licensed"),
         chan=dict(count="Up to 20 MHz LTE carriers, aggregated", spacing="100 kHz raster", width="5-20 MHz (LTE), up to 100 MHz (NR)",
                   formula="NR-ARFCN: F = 5 kHz·N (N < 600000)"),
         tech="LTE-A carrier aggregation, 4×4 MIMO, 256-QAM",
         notes=L("B3 (1800) and B1 (2100) carry most LTE traffic in Europe and Asia. TDD bands use one "
                 "frequency block for both directions, alternating in time.",
                 "B3 (1800) și B1 (2100) transportă cea mai mare parte a traficului LTE în Europa și Asia. Benzile "
                 "TDD folosesc un singur bloc de frecvență pentru ambele sensuri, alternând în timp.")),
    dict(id="nr_c", cat="cell", lo=3300, hi=5000,
         name=L("5G NR C-band (n77 / n78 / n79)", "5G NR banda C (n77 / n78 / n79)"),
         ranges=dict(eu="n78: 3400-3800 MHz", na="n77: 3450-3550, 3700-3980 MHz (C-band)",
                     cn="n78: 3300-3600 MHz, n79: 4800-5000 MHz", jp="n77/n78: 3600-4100 MHz, n79: 4500-4900 MHz"),
         power=dict(eu="UE 23-26 dBm", na="UE 23-26 dBm", cn="UE 26 dBm", jp="UE 23 dBm"),
         access=dict(eu="Licensed TDD", na="Licensed TDD", cn="Licensed TDD", jp="Licensed TDD"),
         chan=dict(count="Typ. 1 × 100 MHz carrier per operator", spacing="15 kHz raster (3-24.25 GHz)",
                   width="up to 100 MHz", formula="NR-ARFCN: F = 3000 MHz + 15 kHz·(N − 600000)"),
         plot=(_nr_n78, 3280, 3820),
         tech="OFDM with 30 kHz subcarriers, massive MIMO (64T64R), beamforming",
         notes=L("The main 5G capacity band. In the USA the C-band (3.7-3.98 GHz) was cleared from satellite TV "
                 "downlinks and borders radio altimeters at 4.2-4.4 GHz, which led to power limits near airports.",
                 "Principala bandă de capacitate 5G. În SUA banda C (3,7-3,98 GHz) a fost eliberată de legăturile "
                 "TV prin satelit și se învecinează cu radioaltimetrele la 4,2-4,4 GHz, ceea ce a dus la limite de "
                 "putere lângă aeroporturi.")),
    dict(id="nr_mm", cat="cell", lo=24250, hi=43500,
         name=L("5G NR mmWave (FR2)", "5G NR unde milimetrice (FR2)"),
         ranges=dict(eu="n258: 24.25-27.5 GHz", na="n260: 37-40 GHz, n261: 27.5-28.35 GHz, n258",
                     cn="n258 (planned 24.75-27.5 GHz)", jp="n257: 27.0-29.5 GHz"),
         power=dict(eu="UE ≤ 43 dBm EIRP (class 3)", na="same", cn="same", jp="same"),
         access=dict(eu="Licensed TDD", na="Licensed TDD", cn="Licensed TDD", jp="Licensed TDD"),
         chan=dict(count="Several × 100-400 MHz", spacing="60 kHz raster", width="50-400 MHz",
                   formula="NR-ARFCN: F = 24250.08 MHz + 60 kHz·(N − 2016667)"),
         tech="120 kHz subcarriers, phased-array beam steering",
         notes=L("Huge bandwidth but short range and easily blocked by bodies and foliage; used for hot-spots "
                 "and fixed wireless access.",
                 "Lățime de bandă uriașă dar rază scurtă, ușor blocată de corpuri și vegetație; folosită pentru "
                 "zone aglomerate și acces fix fără fir.")),

    # ---------------- GNSS ----------------
    dict(id="gnss_l1", cat="gnss", lo=1559, hi=1610,
         name=L("GNSS L1 / E1 / B1 / G1", "GNSS L1 / E1 / B1 / G1"),
         ranges=dict(eu="Worldwide (receive only)", na="Worldwide", cn="Worldwide", jp="Worldwide (+ QZSS)"),
         power=dict(eu="Received ≈ −130 dBm (below the noise)", na="same", cn="same", jp="same"),
         access=dict(eu="RNSS, receive-only", na="-", cn="-", jp="-"),
         chan=dict(count="GPS/Galileo/QZSS/BeiDou-B1C share 1575.42 MHz; GLONASS FDMA 14 channels",
                   spacing="GLONASS 0.5625 MHz", width="GPS C/A 2.046 MHz main lobe; E1 ~4 MHz",
                   formula="GPS L1 = 154 × 10.23 MHz = 1575.42 MHz; GLONASS G1 = 1602 + 0.5625·k MHz (k = −7…+6); BeiDou B1I = 1561.098 MHz"),
         tech="CDMA/BPSK(1) C/A code 1.023 Mchip/s, BOC(1,1) for Galileo E1",
         notes=L("The satellite signal arrives about 20 dB below the thermal noise; the receiver recovers it by "
                 "correlating with the known spreading code (processing gain ≈ 43 dB). Needs a sky view and a "
                 "right-hand circularly polarised antenna for best results.",
                 "Semnalul satelitului ajunge cu circa 20 dB sub zgomotul termic; receptorul îl recuperează prin "
                 "corelare cu codul de împrăștiere cunoscut (câștig de procesare ≈ 43 dB). Are nevoie de vedere "
                 "spre cer și de o antenă cu polarizare circulară dreapta pentru rezultate bune.")),
    dict(id="gnss_l5", cat="gnss", lo=1164, hi=1300,
         name=L("GNSS L5 / E5 / L2 / E6", "GNSS L5 / E5 / L2 / E6"),
         ranges=dict(eu="Worldwide", na="Worldwide", cn="Worldwide", jp="Worldwide"),
         power=dict(eu="Received ≈ −127 dBm (L5)", na="same", cn="same", jp="same"),
         access=dict(eu="RNSS, receive-only", na="-", cn="-", jp="-"),
         chan=dict(count="L5/E5a/B2a 1176.45, E5b 1207.14, L2 1227.60, B3 1268.52, E6 1278.75 MHz", spacing="-",
                   width="~20 MHz (L5, 10.23 Mchip/s)", formula="L5 = 115 × 10.23 MHz; L2 = 120 × 10.23 MHz"),
         tech="Dual-frequency receivers cancel ionospheric delay → ~30 cm accuracy",
         notes=L("Using two frequencies lets the receiver measure and remove the ionospheric delay, which is the "
                 "biggest single-frequency error source.",
                 "Folosirea a două frecvențe permite receptorului să măsoare și să elimine întârzierea ionosferică, "
                 "cea mai mare sursă de eroare la o singură frecvență.")),

    # ---------------- Broadcast ----------------
    dict(id="am", cat="bcast", lo=0.1485, hi=1.7015,
         name=L("AM broadcasting (LW / MW)", "Radiodifuziune AM (UL / UM)"),
         ranges=dict(eu="LW 148.5-283.5 kHz, MW 526.5-1606.5 kHz", na="MW 530-1700 kHz",
                     cn="MW 526.5-1606.5 kHz", jp="MW 526.5-1606.5 kHz"),
         power=dict(eu="Up to 1-2 MW (LW)", na="Up to 50 kW", cn="-", jp="-"),
         access=dict(eu="Licensed", na="Licensed", cn="Licensed", jp="Licensed"),
         chan=dict(count="MW: 120 (9 kHz) / 117 (10 kHz)", spacing="9 kHz (Regions 1/3), 10 kHz (Americas)",
                   width="9-10 kHz (±4.5 kHz audio)", formula="Region 1: f = 531 + 9·n kHz; Americas: f = 540 + 10·n kHz"),
         tech="Double-sideband AM, DRM digital",
         notes=L("Medium waves travel as ground waves by day and reflect off the ionosphere at night, which is why "
                 "distant stations appear after sunset. Many European MW/LW transmitters have closed.",
                 "Undele medii se propagă ca unde de suprafață ziua și se reflectă în ionosferă noaptea, de aceea "
                 "posturile îndepărtate apar după apus. Multe emițătoare UM/UL europene au fost închise.")),
    dict(id="fm", cat="bcast", lo=76, hi=108,
         name=L("FM broadcasting (VHF Band II)", "Radiodifuziune FM (VHF banda II)"),
         ranges=dict(eu="87.5-108 MHz", na="88.1-107.9 MHz (odd decimals)", cn="87-108 MHz",
                     jp="76-95 MHz (90-95 for AM simulcast)"),
         power=dict(eu="Up to ~100 kW ERP", na="Up to 100 kW ERP", cn="-", jp="-"),
         access=dict(eu="Licensed", na="Licensed", cn="Licensed", jp="Licensed"),
         chan=dict(count="~204 (EU 100 kHz raster)", spacing="EU 100 kHz raster (typ. 200-400 kHz apart), US 200 kHz",
                   width="±75 kHz deviation, ~200 kHz occupied", formula="US: f = 88.1 + 0.2·n MHz (n = 0…99)"),
         plot=(_fm, 87.4, 108.1),
         tech="Wideband FM, stereo pilot 19 kHz, RDS 57 kHz subcarrier, pre-emphasis 50 µs (EU) / 75 µs (US)",
         notes=L("An FM receiver's IF is 10.7 MHz, so its local oscillator sits just above the band — a classic "
                 "superheterodyne example.",
                 "Frecvența intermediară a receptorului FM este 10,7 MHz, deci oscilatorul local stă chiar deasupra "
                 "benzii — un exemplu clasic de superheterodină.")),
    dict(id="dab", cat="bcast", lo=174, hi=240,
         name=L("DAB / DAB+ (VHF Band III)", "DAB / DAB+ (VHF banda III)"),
         ranges=dict(eu="174-240 MHz (blocks 5A-13F)", na="Not used (HD Radio in FM band)", cn="Limited",
                     jp="Not used"),
         power=dict(eu="Up to ~10 kW ERP per SFN transmitter", na="-", cn="-", jp="-"),
         access=dict(eu="Licensed, single-frequency networks", na="-", cn="-", jp="-"),
         chan=dict(count="38 blocks", spacing="1.712 MHz", width="1.536 MHz",
                   formula="Block 5A = 174.928 MHz, 12C = 227.360 MHz"),
         tech="COFDM, ~1536 carriers (mode I), each multiplex carries ~10-18 stations",
         notes=L("Several stations share one multiplex; the same frequency is reused by all transmitters in a "
                 "network (SFN), which COFDM tolerates as multipath.",
                 "Mai multe posturi împart un multiplex; aceeași frecvență este refolosită de toate emițătoarele "
                 "rețelei (SFN), iar COFDM tolerează asta ca propagare multicale.")),
    dict(id="dtv", cat="bcast", lo=470, hi=710,
         name=L("Digital TV (UHF Bands IV/V)", "TV digitală (UHF benzile IV/V)"),
         ranges=dict(eu="470-694 MHz (ch 21-48), DVB-T/T2", na="470-608 MHz (ch 14-36), ATSC 1.0/3.0",
                     cn="470-698 MHz, DTMB", jp="470-710 MHz (ch 13-52), ISDB-T"),
         power=dict(eu="Up to ~100 kW ERP", na="Up to 1 MW ERP", cn="-", jp="-"),
         access=dict(eu="Licensed; white-space and PMSE secondary", na="Licensed", cn="Licensed", jp="Licensed"),
         chan=dict(count="EU 28, US 23, JP 40", spacing="EU/CN 8 MHz, US/JP 6 MHz", width="7.6 MHz (DVB-T 8 MHz)",
                   formula="EU: f = 306 + 8·N MHz (N = 21…48); US: f = 389 + 6·N MHz (N = 14…36)"),
         plot=(_dvbt, 466, 698),
         tech="COFDM (DVB-T2, ISDB-T, ATSC 3.0) or 8-VSB (ATSC 1.0)",
         notes=L("The 700 MHz and 800 MHz TV channels were moved to mobile broadband (the 'digital dividend'); "
                 "wireless microphones use the gaps between TV channels.",
                 "Canalele TV de 700 MHz și 800 MHz au fost mutate la banda largă mobilă („dividendul digital”); "
                 "microfoanele wireless folosesc golurile dintre canalele TV.")),

    # ---------------- Amateur / personal ----------------
    dict(id="ham_hf", cat="ham", lo=1.8, hi=29.7,
         name=L("Amateur HF bands (160 m - 10 m)", "Benzi radioamatori HF (160 m - 10 m)"),
         ranges=dict(eu="1.81-2.0, 3.5-3.8, 7.0-7.2, 10.1-10.15, 14.0-14.35, 18.068-18.168, 21.0-21.45, 24.89-24.99, 28.0-29.7 MHz",
                     na="1.8-2.0, 3.5-4.0, 7.0-7.3, 10.1-10.15, 14.0-14.35, 18.068-18.168, 21.0-21.45, 24.89-24.99, 28.0-29.7 MHz",
                     cn="1.8-2.0, 3.5-3.9, 7.0-7.2, … 28.0-29.7 MHz", jp="1.81-1.9125, 3.5-3.575, 7.0-7.2, … 28.0-29.7 MHz"),
         power=dict(eu="Licence class dependent (e.g. 100 W - 1 kW PEP)", na="1.5 kW PEP (Extra)", cn="Class dependent",
                    jp="Class dependent (up to 1 kW)"),
         access=dict(eu="Amateur licence", na="Amateur licence", cn="Amateur licence", jp="Amateur licence"),
         chan=dict(count="9 bands", spacing="Free tuning (band plans by mode)", width="CW ~100 Hz, SSB 2.7 kHz",
                   formula="Band name ≈ wavelength: λ = 300 / f(MHz) m"),
         tech="CW, SSB, FT8, RTTY, AM; skywave propagation around the world",
         notes=L("HF signals bounce between the ionosphere and the ground, so a few watts can reach other "
                 "continents. Propagation depends on the 11-year solar cycle and time of day.",
                 "Semnalele HF ricoșează între ionosferă și sol, deci câțiva wați pot ajunge pe alte continente. "
                 "Propagarea depinde de ciclul solar de 11 ani și de ora zilei.")),
    dict(id="ham_vu", cat="ham", lo=144, hi=450,
         name=L("Amateur 2 m / 70 cm", "Radioamatori 2 m / 70 cm"),
         ranges=dict(eu="144-146 MHz, 430-440 MHz", na="144-148 MHz, 420-450 MHz", cn="144-148 MHz, 430-440 MHz",
                     jp="144-146 MHz, 430-440 MHz"),
         power=dict(eu="Class dependent", na="1.5 kW PEP", cn="Class dependent", jp="Class dependent"),
         access=dict(eu="Amateur licence", na="Amateur licence", cn="Amateur licence", jp="Amateur licence"),
         chan=dict(count="Repeater / simplex plans", spacing="12.5 or 25 kHz", width="FM 12.5 kHz",
                   formula="Repeater shift: 2 m −600 kHz; 70 cm ±5 MHz (US) / −7.6 MHz (EU)"),
         tech="FM, SSB, digital voice (DMR, D-STAR, C4FM), APRS 144.800 MHz (EU) / 144.390 MHz (US)",
         notes=L("Line-of-sight VHF/UHF with repeaters on hills; the classic hand-held radio bands.",
                 "VHF/UHF în linie de vedere cu repetoare pe dealuri; benzile clasice ale stațiilor portabile.")),
    dict(id="pmr", cat="ham", lo=446.0, hi=446.2,
         name=L("PMR446 / FRS walkie-talkies", "Stații PMR446 / FRS"),
         ranges=dict(eu="446.0-446.2 MHz", na="FRS/GMRS 462.55-467.725 MHz", cn="409.75-409.9875 MHz", jp="422 MHz (tokutei shōdenryoku)"),
         power=dict(eu="500 mW ERP", na="FRS 2 W, GMRS 50 W (licensed)", cn="500 mW", jp="10 mW"),
         access=dict(eu="Licence-free, fixed antenna", na="FRS free, GMRS licence", cn="Licence-free", jp="Licence-free"),
         chan=dict(count="16 analogue (+ 32 digital)", spacing="12.5 kHz", width="12.5 kHz (6.25 digital)",
                   formula="f = 446.00625 + 0.0125·(n − 1) MHz (n = 1…16)"),
         plot=(_pmr446, 445.995, 446.205),
         tech="Narrow-band FM, dPMR/DMR tier 1",
         notes=L("A European PMR446 radio is not legal in the USA and vice versa; the bands are different.",
                 "O stație PMR446 europeană nu este legală în SUA și invers; benzile sunt diferite.")),
    dict(id="cb", cat="ham", lo=26.965, hi=27.405,
         name=L("CB radio (27 MHz)", "Radio CB (27 MHz)"),
         ranges=dict(eu="26.965-27.405 MHz", na="26.965-27.405 MHz", cn="26.965-27.405 MHz", jp="26.968-27.144 MHz (8 ch)"),
         power=dict(eu="4 W FM/AM, 12 W PEP SSB", na="4 W AM, 12 W PEP SSB", cn="-", jp="0.5 W"),
         access=dict(eu="Licence-free", na="Licence-free", cn="-", jp="Licence-free"),
         chan=dict(count="40", spacing="10 kHz (with historical gaps)", width="~8 kHz", formula="Ch 1 = 26.965 MHz, ch 19 = 27.185 MHz (road), ch 9 = 27.065 (emergency)"),
         plot=(_cb, 26.95, 27.42),
         tech="AM, FM, SSB",
         notes=L("Channel 23 (27.255 MHz) sits out of order between 22 and 24 for historical reasons (it was a "
                 "radio-control channel).",
                 "Canalul 23 (27,255 MHz) este în afara ordinii între 22 și 24 din motive istorice (era un canal "
                 "de radiocomandă).")),

    # ---------------- Aviation / maritime ----------------
    dict(id="air", cat="nav", lo=108, hi=137,
         name=L("Aeronautical VHF (NAV / COM)", "VHF aeronautic (NAV / COM)"),
         ranges=dict(eu="108-117.975 NAV, 118-136.975 MHz COM", na="same", cn="same", jp="same"),
         power=dict(eu="Aircraft ~20 W", na="same", cn="same", jp="same"),
         access=dict(eu="Aviation licence", na="Aviation licence", cn="Aviation licence", jp="Aviation licence"),
         chan=dict(count="COM: 760 (25 kHz) / 2280 (8.33 kHz)", spacing="8.33 kHz (Europe), 25 kHz elsewhere",
                   width="AM voice", formula="121.500 MHz = international emergency"),
         tech="AM voice (so stronger stations do not capture weaker ones), VOR / ILS localizer 108-118 MHz",
         notes=L("Aviation still uses AM so that two simultaneous transmissions are heard as a squeal instead "
                 "of one silently blocking the other.",
                 "Aviația folosește încă AM pentru ca două emisii simultane să se audă ca un fluierat, în loc ca "
                 "una s-o blocheze pe cealaltă fără să se observe.")),
    dict(id="adsb", cat="nav", lo=960, hi=1215,
         name=L("Transponders / ADS-B / DME", "Transpondere / ADS-B / DME"),
         ranges=dict(eu="1030 MHz interrogation, 1090 MHz reply; DME 960-1215 MHz",
                     na="+ UAT 978 MHz (below 18 000 ft)", cn="1030 / 1090 MHz", jp="1030 / 1090 MHz"),
         power=dict(eu="Transponder 125-500 W peak", na="same", cn="same", jp="same"),
         access=dict(eu="Aviation", na="Aviation", cn="Aviation", jp="Aviation"),
         chan=dict(count="1 (1090 MHz) + 252 DME channels", spacing="DME 1 MHz", width="-",
                   formula="Mode S / ADS-B 1090 MHz, PPM 1 Mbit/s"),
         tech="Pulse-position modulation; decodable with a cheap RTL-SDR",
         notes=L("ADS-B broadcasts position, altitude and speed every second — hobbyists receive it with a USB "
                 "SDR and a 6.9 cm (λ/4) antenna.",
                 "ADS-B transmite poziția, altitudinea și viteza în fiecare secundă — pasionații o recepționează "
                 "cu un SDR USB și o antenă de 6,9 cm (λ/4).")),
    dict(id="marine", cat="nav", lo=156, hi=162.05,
         name=L("Marine VHF / AIS", "VHF maritim / AIS"),
         ranges=dict(eu="156-162.025 MHz", na="156-162.025 MHz", cn="156-162.025 MHz", jp="156-162.025 MHz"),
         power=dict(eu="25 W (1 W low)", na="25 W", cn="25 W", jp="25 W"),
         access=dict(eu="Ship licence / operator certificate", na="-", cn="-", jp="-"),
         chan=dict(count="~57", spacing="25 kHz", width="FM ±5 kHz",
                   formula="Ch 16 = 156.800 MHz (distress); AIS 161.975 / 162.025 MHz"),
         plot=(_marine, 156.0, 157.5),
         tech="FM voice, DSC on ch 70 (156.525 MHz), AIS GMSK 9.6 kbit/s",
         notes=L("Channel 16 is monitored by every ship and coast station for distress and calling.",
                 "Canalul 16 este ascultat de toate navele și stațiile de coastă pentru pericol și apel.")),

    # ---------------- Satellite / radar ----------------
    dict(id="satku", cat="sat", lo=10700, hi=14500,
         name=L("Satellite Ku-band (TV / broadband)", "Satelit banda Ku (TV / internet)"),
         ranges=dict(eu="DL 10.7-12.75 GHz, UL 13.75-14.5 GHz", na="DL 11.7-12.7 GHz, UL 14.0-14.5 GHz",
                     cn="same (ITU)", jp="same (ITU)"),
         power=dict(eu="Satellite EIRP ~50 dBW", na="-", cn="-", jp="-"),
         access=dict(eu="Licensed (receive licence-free)", na="-", cn="-", jp="-"),
         chan=dict(count="Transponders", spacing="~27-36 MHz transponders", width="27-72 MHz",
                   formula="Universal LNB: LO 9.75 GHz (low band) / 10.6 GHz (high band) → IF 950-2150 MHz"),
         tech="DVB-S2(X), LEO constellations (Ku for user terminals, Ka for gateways)",
         notes=L("A satellite dish LNB mixes 10.7-12.75 GHz down to 950-2150 MHz so cheap coax can carry it.",
                 "LNB-ul antenei de satelit coboară 10,7-12,75 GHz la 950-2150 MHz ca să poată fi transportat pe un coaxial ieftin.")),
    dict(id="radar77", cat="sat", lo=76000, hi=81000,
         name=L("Automotive radar 77 / 79 GHz", "Radar auto 77 / 79 GHz"),
         ranges=dict(eu="76-77 GHz (LRR), 77-81 GHz (SRR)", na="76-81 GHz", cn="76-79 GHz", jp="76-77, 77-81 GHz"),
         power=dict(eu="55 dBm peak EIRP (76-77)", na="50 dBm avg EIRP", cn="-", jp="-"),
         access=dict(eu="-", na="-", cn="-", jp="-"),
         chan=dict(count="1", spacing="-", width="up to 4 GHz (79 GHz)", formula="ΔR = c / (2·B): 4 GHz → 3.75 cm"),
         tech="FMCW chirps, MIMO virtual arrays, CMOS single-chip radars",
         notes=L("Replaced the old 24 GHz ultra-wideband car radar; the 4 GHz sweep gives centimetre range "
                 "resolution.",
                 "A înlocuit vechiul radar auto ultra-larg de 24 GHz; baleierea de 4 GHz dă rezoluție de ordinul centimetrilor.")),
]
BAND_BY_ID = {b["id"]: b for b in BANDS}


# ---------------------------------------------------------------------------
# Reference tables
# ---------------------------------------------------------------------------
ITU_BANDS = [
    # (N, symbol, lo Hz, hi Hz, wavelength name, typical uses)
    (1, "ELF", 3, 30, L("100 000-10 000 km", "100 000-10 000 km"),
     L("Submarine communication, power-line hum", "Comunicații cu submarine, brum de rețea")),
    (2, "SLF", 30, 300, L("10 000-1000 km", "10 000-1000 km"), L("Submarines, mains 50/60 Hz", "Submarine, rețea 50/60 Hz")),
    (3, "ULF", 300, 3e3, L("1000-100 km", "1000-100 km"), L("Mine communication, audio range", "Comunicații în mine, domeniu audio")),
    (4, "VLF", 3e3, 30e3, L("100-10 km (myriametric)", "100-10 km (miriametrice)"),
     L("Navy time signals, lightning (sferics), heart-rate straps", "Semnale de timp navale, fulgere, centuri de puls")),
    (5, "LF", 30e3, 300e3, L("10-1 km (kilometric)", "10-1 km (kilometrice)"),
     L("DCF77 time signal, long-wave AM, LF RFID, Qi charging", "Semnal orar DCF77, unde lungi AM, RFID LF, încărcare Qi")),
    (6, "MF", 300e3, 3e6, L("1 km-100 m (hectometric)", "1 km-100 m (hectometrice)"),
     L("Medium-wave AM, maritime, NDB beacons", "Unde medii AM, maritim, radiofaruri NDB")),
    (7, "HF", 3e6, 30e6, L("100-10 m (decametric)", "100-10 m (decametrice)"),
     L("Shortwave, amateur, NFC 13.56 MHz, CB, over-the-horizon radar", "Unde scurte, radioamatori, NFC 13,56 MHz, CB, radar peste orizont")),
    (8, "VHF", 30e6, 300e6, L("10-1 m (metric)", "10-1 m (metrice)"),
     L("FM radio, DAB, airband, marine, 2 m amateur", "Radio FM, DAB, aviație, maritim, radioamatori 2 m")),
    (9, "UHF", 300e6, 3e9, L("1 m-10 cm (decimetric)", "1 m-10 cm (decimetrice)"),
     L("TV, mobile phones, GNSS, Wi-Fi 2.4 GHz, Bluetooth, RFID", "TV, telefonie mobilă, GNSS, Wi-Fi 2,4 GHz, Bluetooth, RFID")),
    (10, "SHF", 3e9, 30e9, L("10-1 cm (centimetric)", "10-1 cm (centimetrice)"),
     L("5G C-band, Wi-Fi 5/6 GHz, satellite TV, radar", "5G banda C, Wi-Fi 5/6 GHz, TV prin satelit, radar")),
    (11, "EHF", 30e9, 300e9, L("10-1 mm (millimetric)", "10-1 mm (milimetrice)"),
     L("5G mmWave, 60 GHz WiGig, 77 GHz car radar, radio astronomy", "5G mmWave, WiGig 60 GHz, radar auto 77 GHz, radioastronomie")),
    (12, "THF", 300e9, 3e12, L("1-0.1 mm (decimillimetric)", "1-0,1 mm (decimilimetrice)"),
     L("Terahertz imaging, spectroscopy, research links", "Imagistică terahertz, spectroscopie, legături experimentale")),
]

IEEE_BANDS = [   # IEEE Std 521 radar letter bands (Hz)
    ("HF", 3e6, 30e6), ("VHF", 30e6, 300e6), ("UHF", 300e6, 1e9), ("L", 1e9, 2e9), ("S", 2e9, 4e9),
    ("C", 4e9, 8e9), ("X", 8e9, 12e9), ("Ku", 12e9, 18e9), ("K", 18e9, 27e9), ("Ka", 27e9, 40e9),
    ("V", 40e9, 75e9), ("W", 75e9, 110e9), ("mm (G)", 110e9, 300e9),
]

NATO_BANDS = [   # NATO / EU (ECM) letter bands (Hz)
    ("A", 0, 250e6), ("B", 250e6, 500e6), ("C", 500e6, 1e9), ("D", 1e9, 2e9), ("E", 2e9, 3e9), ("F", 3e9, 4e9),
    ("G", 4e9, 6e9), ("H", 6e9, 8e9), ("I", 8e9, 10e9), ("J", 10e9, 20e9), ("K", 20e9, 40e9), ("L", 40e9, 60e9),
    ("M", 60e9, 100e9),
]

ITU_REGIONS = L(
    "ITU Region 1: Europe, Africa, Middle East, former USSR.  Region 2: the Americas.  Region 3: Asia-Pacific. "
    "The Radio Regulations table of allocations differs per region, and each country then adds its own rules.",
    "Regiunea ITU 1: Europa, Africa, Orientul Mijlociu, fosta URSS.  Regiunea 2: America.  Regiunea 3: Asia-Pacific. "
    "Tabelul de alocări din Regulamentul Radiocomunicațiilor diferă pe regiuni, iar fiecare țară adaugă apoi propriile reguli.")
