"""
TODO
"""
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

sample_file = Path(__file__).parent.parent.parent.absolute() / Path('input/1_short.srt')
sample_str = io.StringIO(textwrap.dedent('''\
    1
    00:00:00,123 --> 00:00:03,456
    Hi there
    
    2
    00:01:04,843 --> 00:01:05,428
    This is an example of a
    subtitle file in SRT format
'''))


def translate_array(texts: List[str], source_language='auto', target_language='hu'):
    """
    It takes a list of texts and translates them from source language to target language

    :param texts: The list of texts to be translated
    :type texts: List[str]
    :param source_language: The language you want to translate from, defaults to auto (optional)
    :param target_language: The language to translate the text into, defaults to hu (optional)
    :return: A list of translated texts.
    """
    for i, text in enumerate(texts):
        if not text or not isinstance(text, str) or not text.strip():
            texts[i] = " zzz "

        if text.isdigit() or all(i in string.punctuation for i in text):
            texts[i] += " zzz "
    result = GoogleTranslator(source=source_language, target=target_language).translate_batch(texts)

    return result


def split_up(text: str, pieces_count: int = 2) -> List[str]:
    """
    Given a text and a number of pieces, split the text into pieces

    :param text: The text to split up
    :type text: str
    :param pieces_count: The number of pieces to split the text into, defaults to 2
    :type pieces_count: int (optional)
    :return: A list of strings.
    """
    pieces = []

    if pieces_count < 1:
        logging.error("pieces error.")
        sys.exit(1)
    elif pieces_count == 1:
        return [text]

    def get_optimal_split(where: float, p_split_points: List[int]):
        """
        Get the optimal split point from a list of split points

        :param where: the point where you want to split the data
        :type where: float
        :param p_split_points: The list of split points
        :type p_split_points: List[int]
        :return: The optimal split point and the list of split points with the optimal split point removed.
        """
        distance_min = 9999.0
        min_point = None
        for a_split_point in p_split_points:
            distance = abs(where - a_split_point)
            if distance < distance_min:
                distance_min = distance
                min_point = a_split_point

        if min_point:
            p_split_points.remove(min_point)
        return min_point, p_split_points

    len_of_a_piece = len(text) / pieces_count
    optimal_split_positions = [len_of_a_piece * x for x in range(1, pieces_count)]
    indices_object = re.finditer(pattern=r'\w+', string=text)

    possible_split_points = [index.start() for index in indices_object]
    if 0 in possible_split_points:
        possible_split_points.remove(0)

    if len(possible_split_points) + 1 < pieces_count:
        logging.info("[{}]".format(" | ".join(re.split(r'\W+', text).remove(''))))
        logging.error(
            f"There are {len(possible_split_points)} split points and we want "
            f"to split the text '{text}' in {pieces_count} pieces... Giving up.")
        sys.exit(42)

    def get_split_points(optimal_split_positions: List[float],
                         p_possible_split_points: List[int] = possible_split_points):
        """
        Given a list of optimal split positions, return a list of the corresponding split points

        :param optimal_split_positions: The list of optimal split positions
        :type optimal_split_positions: List[float]
        :param p_possible_split_points: List[int] = possible_split_points
        :type p_possible_split_points: List[int]
        :return: The list of optimal split points.
        """
        split_points = []
        for an_optimal_position in optimal_split_positions:
            a_split_point, p_possible_split_points = get_optimal_split(where=an_optimal_position,
                                                                       p_split_points=p_possible_split_points)
            split_points.append(a_split_point)
        return split_points

    start_ind = 0
    for split_point in get_split_points(optimal_split_positions=optimal_split_positions,
                                        p_possible_split_points=possible_split_points):
        pieces.append(text[start_ind:split_point].strip())
        start_ind = split_point
    pieces.append(text[start_ind:].strip())

    logging.debug(f"Splitting up '{text}' in {pieces_count} pieces: {pieces}")

    return pieces


def translate_subtitle_file(input_file=sample_file, target_language='hu'):
    """
    It takes a subtitle file, splits it up into sentences, translates them, and then puts them back together

    :param input_file: The subtitle file to be translated
    :param target_language: The language you want the text to be translated to, defaults to hu (optional)
    :return: The lines of the translated file.
    """
    translation_char_limit = 4000  # 4000
    subtitle = sublib.SubRip(input_file, "utf-8")
    # s2 = copy.deepcopy(subtitle)
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
    for i, a_general in enumerate(general):
        start, end, text = a_general
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
        an_entry = entries_to_be_translated[start:i + 1]
        chars_sum = sum([len(t['text']) for t in an_entry])
        if chars_sum > translation_char_limit - 10 or i == last_i - 1:
            texts = [t['text'] for t in entries_to_be_translated[start:i + 1]]

            time_start = general[entries_to_be_translated[start]['index_end']][1]
            time_end = general[entries_to_be_translated[i]['index_end']][1]

            # strfdelta(time_start, "{hours}:{minutes}:{seconds}")
            logging.info("Translating {} - {}".format(str(time_start)[:-3], str(time_end)[:-3]))

            start = time.time()
            translated = translate_array(texts=texts, target_language=target_language)
            end = time.time()
            logging.info(
                "{} requests in {:.2f} seconds,{:.0f} ch/s, "
                "{:.2f} req/s".format(len(texts),
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
    for i, entry in enumerate(entries_to_be_translated):
        text_long = translated_all[i]
        split_pieces = entry['index_end'] - entry['index_start'] + 1
        texts = split_up(text=text_long, pieces_count=split_pieces)
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
    for i, entry in enumerate(general):
        pieces = int(len(entry[2]) / 40) + 1
        if pieces > 1:
            new_text = "\n".join(split_up(entry[2], pieces_count=pieces))
            entry[2] = new_text

    logging.info("# Phase 5: Saving file")
    empty_subtitle = sublib.SubRip()
    empty_subtitle.set_from_general_format(general)
    lines = empty_subtitle.content
    output_name = str(input_file).replace('.srt', '.out.srt')
    logging.info(f"   Writing output to {output_name}")
    with open(output_name, 'w', encoding='utf-8') as out:
        out.writelines(lines)

    return lines


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # ss = split_up("Ööö, mit csináltál?", 3)
    # ss = split_up("Ööö, mit sdfg sfhg wert sxghsfhgdfhg dfhg g ghdfhg csináltál?", 15)
    # result = translate_array(texts=["hallo welt", "guten morgen",
    # 'Weltfrieden für Manuela'], target_language='hu')

    translate_subtitle_file(input_file=sample_file)
