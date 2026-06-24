import asyncio
import hashlib
import os
import random
import re
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template, request, url_for

try:
    import edge_tts
except Exception:
    edge_tts = None

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "words.db"
AUDIO_DIR = BASE_DIR / "static" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

VOICES = {
    "en-US-JennyNeural": "US Jenny, female",
    "en-US-AriaNeural": "US Aria, female",
    "en-US-GuyNeural": "US Guy, male",
    "en-US-DavisNeural": "US Davis, male",
}
DEFAULT_VOICE = "en-US-JennyNeural"
DEFAULT_GROUP = "Свои слова"

SEED_WORDS = [
("early","рано; ранний","[ur-lee]"),("late","поздно; поздний","[layt]"),("cheap","дешевый","[cheep]"),("expensive","дорогой","[ik-spen-siv]"),("interesting","интересный","[in-truh-sting]"),
("interested","заинтересованный","[in-truh-stid]"),("different","другой; разный","[dif-ruhnt]"),("important","важный","[im-por-tnt]"),("difficult","трудный","[dif-i-kuhlt]"),("easy","легкий","[ee-zee]"),
("beautiful","красивый","[byoo-tuh-ful]"),("ugly","некрасивый","[uhg-lee]"),("big","большой","[big]"),("small","маленький","[smawl]"),("new","новый","[noo]"),
("old","старый","[ohld]"),("young","молодой","[yuhng]"),("long","длинный","[lawng]"),("short","короткий","[short]"),("hot","горячий; жаркий","[haat]"),
("cold","холодный","[kohld]"),("warm","теплый","[worm]"),("cool","прохладный; крутой","[kool]"),("good","хороший","[gud]"),("bad","плохой","[bad]"),
("better","лучше","[bet-er]"),("best","лучший","[best]"),("worse","хуже","[wurs]"),("worst","худший","[wurst]"),("fast","быстрый","[fast]"),
("slow","медленный","[sloh]"),("happy","счастливый","[hap-ee]"),("sad","грустный","[sad]"),("angry","злой","[ang-gree]"),("tired","уставший","[tyerd]"),
("hungry","голодный","[huhn-gree]"),("thirsty","испытывающий жажду","[thur-stee]"),("busy","занятый","[biz-ee]"),("free","свободный; бесплатный","[free]"),("ready","готовый","[red-ee]"),
("clean","чистый","[kleen]"),("dirty","грязный","[dur-tee]"),("strong","сильный","[strawng]"),("weak","слабый","[week]"),("rich","богатый","[rich]"),
("poor","бедный","[poor]"),("kind","добрый","[kynd]"),("funny","смешной","[fun-ee]"),("serious","серьезный","[seer-ee-us]"),("quiet","тихий","[kwy-uht]"),
("loud","громкий","[lowd]"),("right","правый; правильный","[ryt]"),("wrong","неправильный","[rawng]"),("true","правда; верный","[troo]"),("false","ложный","[fawls]"),
("house","дом","[hows]"),("home","дом; домой","[hohm]"),("room","комната","[room]"),("kitchen","кухня","[kich-in]"),("bathroom","ванная","[bath-room]"),
("bedroom","спальня","[bed-room]"),("door","дверь","[dor]"),("window","окно","[win-doh]"),("table","стол","[tay-buhl]"),("chair","стул","[chair]"),
("bed","кровать","[bed]"),("book","книга","[buk]"),("pen","ручка","[pen]"),("pencil","карандаш","[pen-suhl]"),("paper","бумага","[pay-per]"),
("bag","сумка","[bag]"),("phone","телефон","[fohn]"),("computer","компьютер","[kuhm-pyoo-ter]"),("car","машина","[kar]"),("bus","автобус","[bus]"),
("train","поезд","[trayn]"),("plane","самолет","[playn]"),("bike","велосипед","[byk]"),("street","улица","[street]"),("city","город","[sit-ee]"),
("country","страна; деревня","[kuhn-tree]"),("school","школа","[skool]"),("teacher","учитель","[tee-cher]"),("student","ученик; студент","[stoo-dnt]"),("lesson","урок","[les-uhn]"),
("question","вопрос","[kwes-chuhn]"),("answer","ответ","[an-ser]"),("friend","друг","[frend]"),("family","семья","[fam-uh-lee]"),("mother","мама","[muh-ther]"),
("father","папа","[fah-ther]"),("brother","брат","[bruh-ther]"),("sister","сестра","[sis-ter]"),("child","ребенок","[chyld]"),("children","дети","[chil-druhn]"),
("man","мужчина","[man]"),("woman","женщина","[wum-uhn]"),("people","люди","[pee-puhl]"),("person","человек","[pur-suhn]"),("name","имя","[naym]"),
("food","еда","[food]"),("water","вода","[waw-ter]"),("coffee","кофе","[kaw-fee]"),("tea","чай","[tee]"),("milk","молоко","[milk]"),
("bread","хлеб","[bred]"),("cheese","сыр","[cheez]"),("meat","мясо","[meet]"),("fish","рыба","[fish]"),("chicken","курица","[chik-in]"),
("rice","рис","[rys]"),("potato","картофель","[puh-tay-toh]"),("apple","яблоко","[ap-uhl]"),("banana","банан","[buh-nan-uh]"),("orange","апельсин","[or-inj]"),
("soup","суп","[soop]"),("salad","салат","[sal-uhd]"),("breakfast","завтрак","[brek-fuhst]"),("lunch","обед","[lunch]"),("dinner","ужин","[din-er]"),
("morning","утро","[mor-ning]"),("afternoon","день после полудня","[af-ter-noon]"),("evening","вечер","[eev-ning]"),("night","ночь","[nyt]"),("today","сегодня","[tuh-day]"),
("tomorrow","завтра","[tuh-mor-oh]"),("yesterday","вчера","[yes-ter-day]"),("week","неделя","[week]"),("month","месяц","[muhnth]"),("year","год","[yeer]"),
("time","время","[tym]"),("day","день","[day]"),("hour","час","[ow-er]"),("minute","минута","[min-it]"),("second","секунда; второй","[sek-uhnd]"),
("Monday","понедельник","[muhn-day]"),("Tuesday","вторник","[tooz-day]"),("Wednesday","среда","[wenz-day]"),("Thursday","четверг","[thurz-day]"),("Friday","пятница","[fry-day]"),
("Saturday","суббота","[sat-er-day]"),("Sunday","воскресенье","[sun-day]"),("work","работа; работать","[wurk]"),("job","работа","[jaab]"),("shop","магазин","[shaap]"),
("store","магазин","[stor]"),("money","деньги","[muhn-ee]"),("price","цена","[prys]"),("buy","покупать","[by]"),("sell","продавать","[sel]"),
("pay","платить","[pay]"),("open","открывать; открытый","[oh-puhn]"),("close","закрывать; близкий","[klohz]"),("start","начинать","[start]"),("finish","заканчивать","[fin-ish]"),
("begin","начинать","[bih-gin]"),("end","конец; заканчивать","[end]"),("go","идти; ехать","[goh]"),("come","приходить","[kuhm]"),("live","жить","[liv]"),
("like","любить; нравиться","[lyk]"),("love","любить","[luhv]"),("want","хотеть","[waant]"),("need","нуждаться","[need]"),("have","иметь","[hav]"),
("make","делать; создавать","[mayk]"),("do","делать","[doo]"),("take","брать","[tayk]"),("give","давать","[giv]"),("get","получать","[get]"),
("put","класть","[put]"),("find","находить","[fynd]"),("know","знать","[noh]"),("think","думать","[thingk]"),("understand","понимать","[uhn-der-stand]"),
("learn","учить; изучать","[lern]"),("study","учиться; изучать","[stuh-dee]"),("read","читать","[reed]"),("write","писать","[ryt]"),("speak","говорить","[speek]"),
("listen","слушать","[lis-uhn]"),("watch","смотреть","[waach]"),("see","видеть","[see]"),("look","смотреть","[luk]"),("hear","слышать","[heer]"),
("ask","спрашивать","[ask]"),("tell","рассказывать; сказать","[tel]"),("say","сказать","[say]"),("call","звонить; называть","[kawl]"),("help","помогать","[help]"),
("try","пытаться","[try]"),("use","использовать","[yooz]"),("play","играть","[play]"),("run","бежать","[ruhn]"),("walk","ходить","[wawk]"),
("sit","сидеть","[sit]"),("stand","стоять","[stand]"),("sleep","спать","[sleep]"),("wake","просыпаться","[wayk]"),("eat","есть","[eet]"),
("drink","пить","[dringk]"),("cook","готовить","[kuk]"),("clean","убирать; чистить","[kleen]"),("drive","водить машину","[dryv]"),("travel","путешествовать","[trav-uhl]"),
("wait","ждать","[wayt]"),("move","двигаться","[moov]"),("turn","поворачивать","[turn]"),("bring","приносить","[bring]"),("send","отправлять","[send]"),
("show","показывать","[shoh]"),("meet","встречать","[meet]"),("remember","помнить","[rih-mem-ber]"),("forget","забывать","[fer-get]"),("choose","выбирать","[chooz]"),
("change","менять","[chaynj]"),("keep","держать; сохранять","[keep]"),("leave","уходить; оставлять","[leev]"),("feel","чувствовать","[feel]"),("become","становиться","[bih-kuhm]"),
("be","быть","[bee]"),("am","есть; являюсь","[am]"),("is","есть; является","[iz]"),("are","есть; являются","[ar]"),("was","был","[wuhz]"),
("were","были","[wur]"),("can","мочь","[kan]"),("could","мог бы","[kud]"),("should","следует","[shud]"),("would","бы; хотел бы","[wud]"),
("will","будет","[wil]"),("must","должен","[muhst]"),("may","может","[may]"),("might","может быть","[myt]"),("yes","да","[yes]"),
("no","нет","[noh]"),("not","не","[naat]"),("very","очень","[ver-ee]"),("too","тоже; слишком","[too]"),("also","также","[awl-soh]"),
("only","только","[ohn-lee]"),("always","всегда","[awl-wayz]"),("usually","обычно","[yoo-zhoo-uh-lee]"),("often","часто","[aw-fuhn]"),("sometimes","иногда","[suhm-tymz]"),
("never","никогда","[nev-er]"),("here","здесь","[heer]"),("there","там","[thair]"),("where","где","[wair]"),("when","когда","[wen]"),
("why","почему","[wy]"),("what","что","[wuht]"),("who","кто","[hoo]"),("which","который","[wich]"),("how","как","[how]"),
("this","это; этот","[this]"),("that","то; тот","[that]"),("these","эти","[theez]"),("those","те","[thohz]"),("my","мой","[my]"),
("your","твой; ваш","[yor]"),("his","его","[hiz]"),("her","ее","[hur]"),("our","наш","[ow-er]"),("their","их","[thair]"),
("one","один","[wuhn]"),("two","два","[too]"),("three","три","[three]"),("four","четыре","[for]"),("five","пять","[fyv]"),
("six","шесть","[siks]"),("seven","семь","[sev-uhn]"),("eight","восемь","[ayt]"),("nine","девять","[nyn]"),("ten","десять","[ten]"),
("first","первый","[furst]"),("last","последний","[last]"),("next","следующий","[nekst]"),("same","такой же","[saym]"),("other","другой","[uh-ther]"),
("again","снова","[uh-gen]"),("together","вместе","[tuh-geth-er]"),("alone","один; в одиночку","[uh-lohn]"),("near","рядом","[neer]"),("far","далеко","[far]"),
("inside","внутри","[in-syd]"),("outside","снаружи; на улице","[owt-syd]"),("under","под","[uhn-der]"),("over","над; через","[oh-ver]"),("between","между","[bih-tween]"),
("after","после","[af-ter]"),("before","до; перед","[bih-for]"),("because","потому что","[bih-kuhz]"),("but","но","[buht]"),("and","и","[and]"),
("or","или","[or]"),("with","с","[with]"),("without","без","[with-owt]"),("for","для; за","[for]"),("from","из; от","[fruhm]"),
("to","к; в","[too]"),("in","в","[in]"),("on","на","[aan]"),("at","у; в","[at]"),("about","о; примерно","[uh-bowt]"),
("cat","кот","[kat]"),("dog","собака","[dawg]"),("bird","птица","[burd]"),("horse","лошадь","[hors]"),("cow","корова","[kow]"),
("rain","дождь","[rayn]"),("snow","снег","[snoh]"),("sun","солнце","[suhn]"),("wind","ветер","[wind]"),("weather","погода","[weth-er]"),
("music","музыка","[myoo-zik]"),("movie","фильм","[moo-vee]"),("game","игра","[gaym]"),("sport","спорт","[sport]"),("art","искусство","[art]"),
("doctor","врач","[daak-ter]"),("nurse","медсестра","[nurs]"),("engineer","инженер","[en-juh-neer]"),("driver","водитель","[dry-ver]"),("worker","работник","[wur-ker]"),
("office","офис","[aw-fis]"),("hospital","больница","[haas-pi-tl]"),("restaurant","ресторан","[res-tuh-rahnt]"),("bank","банк","[bangk]"),("market","рынок","[mar-kit]"),
("problem","проблема","[prah-bluhm]"),("idea","идея","[y-dee-uh]"),("plan","план","[plan]"),("reason","причина","[ree-zuhn]"),("result","результат","[rih-zuhlt]"),
("example","пример","[ig-zam-puhl]"),("story","история","[stor-ee]"),("language","язык","[lang-gwij]"),("word","слово","[wurd]"),("sentence","предложение","[sen-tuhns]"),
("grammar","грамматика","[gram-er]"),("pronunciation","произношение","[pruh-nuhn-see-ay-shuhn]"),("meaning","значение","[mee-ning]"),("translation","перевод","[trans-lay-shuhn]"),("practice","практика","[prak-tis]"),
("exercise","упражнение","[ek-ser-syz]"),("test","тест","[test]"),("mistake","ошибка","[mi-stayk]"),("correct","правильный; исправлять","[kuh-rekt]"),("wrong","неправильный","[rawng]"),
("repeat","повторять","[rih-peet]"),("random","случайный","[ran-duhm]"),("sound","звук","[sownd]"),("voice","голос","[voys]"),("button","кнопка","[buht-uhn]")
]


CATEGORY_RANGES = [
    ("Прилагательные", 0, 54),
    ("Дом, вещи и транспорт", 55, 80),
    ("Школа и люди", 81, 99),
    ("Еда и напитки", 100, 119),
    ("Время", 120, 134),
    ("Дни недели", 135, 141),
    ("Работа и покупки", 142, 156),
    ("Глаголы", 157, 219),
    ("To be и модальные", 220, 233),
    ("Частые слова", 234, 264),
    ("Числа и порядок", 265, 279),
    ("Место, предлоги и связки", 280, 304),
    ("Животные и погода", 305, 314),
    ("Хобби, места и профессии", 315, 329),
    ("Учеба и язык", 330, 354),
]


def build_seed_group_map():
    result = {}
    for group_name, start, end in CATEGORY_RANGES:
        for word, _, _ in SEED_WORDS[start:end + 1]:
            clean_key = str(word).strip().replace("’", "'").replace("‘", "'").replace("`", "'").lower()
            result[clean_key] = group_name
    return result


SEED_GROUP_BY_WORD = build_seed_group_map()


def seed_group_for_word(word: str) -> str:
    clean_key = str(word).strip().replace("’", "'").replace("‘", "'").replace("`", "'").lower()
    return SEED_GROUP_BY_WORD.get(clean_key, DEFAULT_GROUP)



def clean_word(text: str) -> str:
    text = (text or "").strip()
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'")
    text = re.sub(r"\s+", " ", text)
    return text


def clean_group(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text or DEFAULT_GROUP


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_column(conn, table, column, definition):
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def get_or_create_group(conn, name):
    name = clean_group(name)
    row = conn.execute("SELECT id FROM groups WHERE lower(name)=lower(?)", (name,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO groups (name) VALUES (?)", (name,))
    return cur.lastrowid


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            translation TEXT DEFAULT '',
            transcription TEXT DEFAULT '',
            group_id INTEGER,
            known INTEGER DEFAULT 0,
            shown_count INTEGER DEFAULT 0,
            known_count INTEGER DEFAULT 0,
            unknown_count INTEGER DEFAULT 0,
            FOREIGN KEY(group_id) REFERENCES groups(id)
        )
    """)
    ensure_column(conn, "words", "group_id", "INTEGER")

    default_id = get_or_create_group(conn, DEFAULT_GROUP)
    group_cache = {DEFAULT_GROUP: default_id}
    for group_name, _, _ in CATEGORY_RANGES:
        group_cache[group_name] = get_or_create_group(conn, group_name)

    # Старые слова без группы отправляем в пользовательскую группу
    conn.execute("UPDATE words SET group_id=? WHERE group_id IS NULL", (default_id,))

    for word, translation, transcription in SEED_WORDS:
        word_clean = clean_word(word)
        group_name = seed_group_for_word(word_clean)
        gid = group_cache.get(group_name) or get_or_create_group(conn, group_name)
        conn.execute(
            "INSERT OR IGNORE INTO words (word, translation, transcription, group_id) VALUES (?, ?, ?, ?)",
            (word_clean, translation, transcription, gid)
        )
        conn.execute("UPDATE words SET group_id=? WHERE lower(word)=lower(?)", (gid, word_clean))
    conn.commit()
    conn.close()


def row_to_dict(row):
    return dict(row) if row else None


@app.route("/")
def index():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    known = conn.execute("SELECT COUNT(*) FROM words WHERE known=1").fetchone()[0]
    groups = conn.execute("SELECT id, name FROM groups ORDER BY name COLLATE NOCASE").fetchall()
    conn.close()
    return render_template(
        "index.html",
        total=total,
        known=known,
        voices=VOICES,
        default_voice=DEFAULT_VOICE,
        groups=[row_to_dict(g) for g in groups]
    )


@app.route("/api/groups")
def api_groups():
    conn = get_db()
    rows = conn.execute("""
        SELECT g.id, g.name, COUNT(w.id) AS word_count
        FROM groups g
        LEFT JOIN words w ON w.group_id = g.id
        GROUP BY g.id
        ORDER BY g.name COLLATE NOCASE
    """).fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows])


@app.route("/api/groups/add", methods=["POST"])
def api_add_group():
    data = request.get_json(silent=True) or request.form
    name = clean_group(data.get("name", ""))
    if not name:
        return jsonify({"error": "Введите название группы"}), 400
    conn = get_db()
    gid = get_or_create_group(conn, name)
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "id": gid, "name": name})


@app.route("/api/random")
def api_random():
    group_id = request.args.get("group_id", "all")
    conn = get_db()
    if group_id and group_id != "all":
        rows = conn.execute("SELECT * FROM words WHERE group_id=?", (group_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM words").fetchall()
    if not rows:
        conn.close()
        return jsonify({"error": "В этой группе пока нет слов"}), 404
    row = random.choice(rows)
    conn.execute("UPDATE words SET shown_count = shown_count + 1 WHERE id=?", (row["id"],))
    conn.commit()
    fresh = conn.execute("""
        SELECT w.*, g.name AS group_name
        FROM words w LEFT JOIN groups g ON g.id = w.group_id
        WHERE w.id=?
    """, (row["id"],)).fetchone()
    conn.close()
    return jsonify(row_to_dict(fresh))


@app.route("/api/words")
def api_words():
    group_id = request.args.get("group_id", "all")
    conn = get_db()
    if group_id and group_id != "all":
        rows = conn.execute("""
            SELECT w.*, g.name AS group_name
            FROM words w LEFT JOIN groups g ON g.id = w.group_id
            WHERE w.group_id=?
            ORDER BY w.word COLLATE NOCASE
        """, (group_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT w.*, g.name AS group_name
            FROM words w LEFT JOIN groups g ON g.id = w.group_id
            ORDER BY w.word COLLATE NOCASE
        """).fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows])


@app.route("/api/add", methods=["POST"])
def api_add():
    data = request.get_json(silent=True) or request.form
    word = clean_word(data.get("word", ""))
    translation = (data.get("translation", "") or "").strip()
    transcription = (data.get("transcription", "") or "").strip()
    group_id = data.get("group_id")
    new_group = clean_group(data.get("new_group", "")) if data.get("new_group") else ""
    if not word:
        return jsonify({"error": "Введите слово"}), 400
    conn = get_db()
    if new_group:
        gid = get_or_create_group(conn, new_group)
    elif group_id and group_id != "all":
        gid = int(group_id)
    else:
        gid = get_or_create_group(conn, DEFAULT_GROUP)
    try:
        conn.execute(
            "INSERT INTO words (word, translation, transcription, group_id) VALUES (?, ?, ?, ?)",
            (word, translation, transcription, gid)
        )
    except sqlite3.IntegrityError:
        conn.execute(
            "UPDATE words SET translation=?, transcription=?, group_id=? WHERE lower(word)=lower(?)",
            (translation, transcription, gid, word)
        )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/mark", methods=["POST"])
def api_mark():
    data = request.get_json(silent=True) or {}
    word_id = data.get("id")
    status = data.get("status")
    if status not in ("known", "unknown"):
        return jsonify({"error": "bad status"}), 400
    conn = get_db()
    if status == "known":
        conn.execute("UPDATE words SET known=1, known_count=known_count+1 WHERE id=?", (word_id,))
    else:
        conn.execute("UPDATE words SET known=0, unknown_count=unknown_count+1 WHERE id=?", (word_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/delete/<int:word_id>", methods=["POST"])
def api_delete(word_id):
    conn = get_db()
    conn.execute("DELETE FROM words WHERE id=?", (word_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/speak", methods=["POST"])
def speak():
    if edge_tts is None:
        return jsonify({"error": "edge-tts не установлен. Выполни: py -m pip install edge-tts"}), 500

    data = request.get_json(silent=True) or {}
    text = clean_word(data.get("text", ""))
    voice = data.get("voice", DEFAULT_VOICE)
    if voice not in VOICES:
        voice = DEFAULT_VOICE
    if not text:
        return jsonify({"error": "Пустой текст"}), 400

    safe_key = hashlib.md5(f"{voice}|{text}".encode("utf-8")).hexdigest()
    audio_path = AUDIO_DIR / f"{safe_key}.mp3"

    if not audio_path.exists():
        try:
            async def make_audio():
                communicate = edge_tts.Communicate(text=text, voice=voice, rate="+0%", volume="+0%")
                await communicate.save(str(audio_path))
            asyncio.run(make_audio())
        except Exception as e:
            return jsonify({"error": f"Озвучка не запустилась: {type(e).__name__}: {e}"}), 500

    return jsonify({"audio_url": url_for("static", filename=f"audio/{audio_path.name}")})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
