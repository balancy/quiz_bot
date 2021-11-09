import re


def extract_quiz_dictionary_from_file(filename: str) -> dict:
    with open(filename, mode='r', encoding='KOI8-R') as file:
        file_content = file.read().replace('\n\n', '\n').replace('\n', ' ')

    quiz_items = re.findall(
        r'Вопрос \d+: (.+?) Ответ: (.+?) Автор:',
        file_content,
    )

    return {question: answer for (question, answer, _, _) in quiz_items}


if __name__ == '__main__':
    filename = 'quiz/1vs1200.txt'
    quiz_dictionary = extract_quiz_dictionary_from_file(filename)
    print(quiz_dictionary)
