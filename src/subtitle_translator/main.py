import copy
import datetime
import io
import logging
import re
import string
import sys
import textwrap
import time
from datetime import timedelta
from pathlib import Path
from typing import List

import sublib
from deep_translator import GoogleTranslator

# https://pypi.org/project/sublib/
# https://pypi.org/project/deep-translator

sample_file = Path(__file__).parent.parent.parent.absolute() / Path('input/1.srt')
sample_str = io.StringIO(textwrap.dedent('''\
    1
    00:00:00,123 --> 00:00:03,456
    Hi there
    
    2
    00:01:04,843 --> 00:01:05,428
    This is an example of a
    subtitle file in SRT format
'''))


def subtitle_parser_test():
    def get_subtitles_from_file(inp: str):
        import subtitle_parser
        with open(inp, 'r', encoding='utf-8') as input_file:
            parser = subtitle_parser.SrtParser(input_file)
            parser.parse()
            parser.print_warnings()

        return parser.subtitles

    def get_subtitles_from_str(inp: str):
        from subtitle_parser import SrtParser
        parser = SrtParser(inp)
        parser.parse()
        parser.print_warnings()

        return parser.subtitles

    subtitles = get_subtitles_from_str(sample_str)
    subtitles = get_subtitles_from_file(sample_file)
    texts = [subtitle.text for subtitle in subtitles]
    translated = GoogleTranslator(source='german', target='english').translate_batch(texts)


def translate_array(texts, source_language='auto', target_language='hu'):
    for i in range(len(texts)):
        text = texts[i]
        if not text or not isinstance(text, str) or not text.strip():
            texts[i] = " zzz "

        if text.isdigit() or all(i in string.punctuation for i in text):
            texts[i] += " zzz "
    result = GoogleTranslator(source=source_language, target=target_language).translate_batch(texts)

    return result


def split_up(text: str, pieces: int = 2) -> List[str]:
    ps = []
    if pieces == 1:
        return [text]
    elif pieces < 1:
        logging.error("pieces error.")
        exit(1)

    def get_optimal_split(where: float, p_split_points: List[int]):
        minnn = 9999.0
        for a_split_point in p_split_points:
            d = abs(where - a_split_point)
            if d < minnn:
                minnn = d
                min_point = a_split_point

        p_split_points.remove(min_point)
        return min_point, p_split_points

    len_of_a_piece = len(text) / pieces
    optimal_split_positions = [len_of_a_piece * x for x in range(1, pieces)]
    indices_object = re.finditer(pattern=r'\w+', string=text)

    possible_split_points = [index.start() for index in indices_object]
    if 0 in possible_split_points: possible_split_points.remove(0)

    if len(possible_split_points) + 1 < pieces:
        p = re.split(r'\W+', text)
        p.remove('')
        logging.info("[{}]".format(" | ".join(p)))
        logging.error(
            f"There are {len(possible_split_points)} split points and we want to split the text '{text}' in {pieces} "
            f"pieces... Giving up.")
        sys.exit(42)

    def get_split_points(optimal_split_positions: List[float],
                         p_possible_split_points: List[int] = possible_split_points):
        split_points = []
        for o in optimal_split_positions:
            sp, p_possible_split_points = get_optimal_split(where=o, p_split_points=p_possible_split_points)
            split_points.append(sp)
        return split_points

    start_ind = 0
    for split_point in get_split_points(optimal_split_positions=optimal_split_positions,
                                        p_possible_split_points=possible_split_points):
        ps.append(text[start_ind:split_point].strip())
        start_ind = split_point
    ps.append(text[start_ind:].strip())

    logging.debug(f"Splitting up '{text}' in {pieces} pieces: {ps}")

    return ps


def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


def translate_subtitle_file(input=sample_file, target_language='hu'):
    translation_char_limit = 4000  # 4000
    subtitle = sublib.SubRip(input, "utf-8")
    s2 = copy.deepcopy(subtitle)
    general = subtitle.get_general_format()

    def is_end_of_sentence(text: str):
        return text.endswith('.') or text.endswith('?') or text.endswith('!')

    def starts_with_lowercase(text: str):
        first_char = text[0]
        return first_char.isalpha() and first_char.islower()

    translated_all = []
    entries_to_be_translated = []

    entry = {'index_start': 0, 'index_end': 0, 'text': ''}

    logging.info("# Phase 1: Prepare translation: Join entries to sentences.")
    for i in range(len(general)):
        start, end, text = general[i]
        text = text.replace('|', ' ').replace('  ', '')
        if len(entry['text']) > 0:
            entry['text'] += ' '
        entry['text'] += text

        if len(general) > i + 1:
            start_next = general[i + 1][0]
        else:
            start_next = end + timedelta(100)

        silence_to_next = start_next - end
        if is_end_of_sentence(text) or silence_to_next.seconds > 1:
            entry['index_end'] = i
            entries_to_be_translated.append(entry)
            entry = {'index_start': i + 1, 'index_end': i + 1, 'text': ''}

    logging.info("# Phase 2: Translate (5000 char limitation)")
    start = 0
    last_i = len(entries_to_be_translated)
    translated_all = []

    for i in range(last_i):
        a = entries_to_be_translated[start:i + 1]
        chars_sum = sum([len(t['text']) for t in a])
        if chars_sum > translation_char_limit - 10 or i == last_i - 1:
            texts = [t['text'] for t in entries_to_be_translated[start:i + 1]]

            time_start: datetime.timedelta = general[entries_to_be_translated[start]['index_end']][1]
            time_end: datetime.timedelta = general[entries_to_be_translated[i]['index_end']][1]

            # strfdelta(time_start, "{hours}:{minutes}:{seconds}")
            logging.info("Translating {} - {}".format(str(time_start)[:-3], str(time_end)[:-3]))

            start = time.time()
            translated = translate_array(texts=texts, target_language='hu')
            end = time.time()
            logging.info(
                "{} requests in {:.2f} seconds,{:.0f} ch/s, {:.2f} req/s".format(len(texts),
                                                                                                end - start,
                                                                                                float(chars_sum) / (
                                                                                                        end - start),
                                                                                                float(len(texts)) / (
                                                                                                        end - start)))

            for res in zip(texts, translated):
                logging.debug(f" [{res[0]}] -> [{res[1]}]")

            translated_all.extend(translated)
            # print(translated)
            start = i + 1

    logging.info("# Phase 3: Split up sentences (undo #1)")
    for i in range(len(entries_to_be_translated)):
        entry = entries_to_be_translated[i]
        text_long = translated_all[i]
        split_pieces = entry['index_end'] - entry['index_start'] + 1
        texts = split_up(text=text_long, pieces=split_pieces)
        if len(texts) != split_pieces:
            logging.error("bahh")

        insert_start = entry['index_start']
        insert_end = entry['index_end']
        for i2 in range(insert_end - insert_start + 1):
            iii = insert_start + i2 - 1
        if iii < len(general) - 1:
            general[iii][2] = texts[i2]
        else:
            logging.error("Index overrun.")
        sys.exit(1)

    logging.info("# Phase 4: Split up lines")
    for i in range(len(general)):
        pieces = int(len(general[i][2]) / 40) + 1
    if pieces > 1:
        new_text = "\n".join(split_up(general[i][2], pieces=pieces))
    general[i][2] = new_text

    logging.info("# Phase 5: Saving file")
    empty_subtitle = sublib.SubRip()
    empty_subtitle.set_from_general_format(general)
    lines = empty_subtitle.content
    with open(str(input).replace('.srt', '.out.srt'), 'w', encoding='utf-8') as out:
        out.writelines(lines)

    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # ss = split_up("Ööö, mit csináltál?", 3)
    # ss = split_up("Ööö, mit sdfg sfhg wert sxghsfhgdfhg dfhg g ghdfhg csináltál?", 15)
    # result = translate_array(texts=["hallo welt", "guten morgen", 'Weltfrieden für Manuela'], target_language='hu')

    translate_subtitle_file(input=sample_file)

    pass
