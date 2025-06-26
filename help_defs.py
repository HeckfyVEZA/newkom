import pandas as pd
from docx2txt import process
import re
import io
from itertools import dropwhile, takewhile
from data_freq import frequency_manager
import pdfplumber

def sashQUA(main_system_name:str, the_mask = r'\d?[A-Za-zА-Яа-яЁё]\D?\D?\D?\D?\S?\S?\S?\S?\d{1,}[А-Яа-яЁё]?'):
    try:
        all_system_names = []
        for system_name in main_system_name.replace("-", " - ").split(','):
            system_name_all = re.findall(the_mask, system_name.strip(), re.IGNORECASE)
            system_name_all = system_name_all if system_name_all else [main_system_name]
            if len(system_name_all) > 1:
                all_positions_in_system_name = tuple(tuple(filter(None, re.findall(r'(\D?|\d+)', sys_name, re.IGNORECASE))) for sys_name in system_name_all)
                system_condition = lambda x: x[0] == x[1]
                before_changing_part = ''.join(el[0] for el in takewhile(system_condition, zip(all_positions_in_system_name[0], all_positions_in_system_name[1])))
                after_changing_part = dropwhile(system_condition, zip(all_positions_in_system_name[0], all_positions_in_system_name[1]))
                changing_part_start, changing_part_thend = next(after_changing_part)
                after_changing_part = ''.join(el[0] for el in after_changing_part)
                all_system_names += [f"{before_changing_part}{'0' * (min(len(changing_part_start), len(changing_part_thend)) - len(str(i)))}{i}{after_changing_part}" for i in range(int(changing_part_start), int(changing_part_thend) + 1)]
            else:
                all_system_names += system_name_all
        return len(all_system_names)
    except:
        return 1

def information_from_file(uploaded_file):
    try:
        canal_dataframe = pd.DataFrame()
        info_file = [item for item in process(uploaded_file).split('\n') if item]
        infofreq = list(map(lambda item: re.findall(r'Эл.двиг: Ny=(\d{1,3},?\d{1,3}) кВт; Uпит=~?(\d{1,3}) ?В; Iпот=(\d{1,3},?\d{1,3}) A', item), info_file))
        infofreq = [list(map(lambda x: float(x.replace(',', '.')), item[0])) for item in list(infofreq) if item]
        freg_must_be = list(map(lambda item: re.findall(r"Регулятор оборотов двигателя .+ вентилятора: (.{2,3})", item), info_file))
        freg_must_be = [item for item in list(freg_must_be) if item]
        try:
            infofreq = [infofreq[i] + [freg_must_be[i][0]] for i in range(len(infofreq))]
        except:
            pass
        corregs = []
        for item in infofreq:
            try:
                p, v, c, must = item
            
                if must.lower() == 'да':
                    corregs += [frequency_manager.query('voltage==@v and current>@c and power >= @p').iloc[0]['name']]
            except:
                pass
        main_blocks = map(lambda item: re.findall(r'\d{1,2}\. (.*)', item), info_file)
        main_blocks = [item[0] for item in list(main_blocks) if item]
        main_indexes = map(lambda item: re.findall(r'Индекс: ?+(.+)[;, ]?', item), info_file)
        main_indexes = [item[0].split(";")[0] for item in list(main_indexes) if item]
        main_indexes = [item[:-1] if item[-1] == '.' else item for item in main_indexes]
        extra_blocks = map(lambda item: re.findall(r': ?(.+) {1,2}- {1,2}(.+) ', item), info_file)
        extra_blocks = [item[0] for item in list(extra_blocks) if item]
        main_correct_blocks = list(zip(list(map(lambda x: x.split()[0], main_blocks)), main_indexes))
        main_correct_blocks = list(map(lambda x: ' '.join(x), main_correct_blocks))
        main_correct_blocks = [item+"-G4" if item.startswith('Фильтр Канал-ФКК-') and len(item)==20 else item for item in main_correct_blocks]
        main_correct_blocks = [item+",0" if item.startswith('Воздухонагреватель Канал-ЭКВ-К-') and not ',' in item else item for item in main_correct_blocks]
        canal_dataframe['block'] = main_correct_blocks
        canal_dataframe['quantity'] = 1
        extra_correct_blocks = [("Хомут " + extra[0] if 'МК' in extra[0] else "Адаптер "+ extra[0] if extra[0].startswith('К-') else "Гибкая вставка " + extra[0], int(extra[1])) for extra in extra_blocks]
        for item in extra_correct_blocks:
            canal_dataframe.loc[len(canal_dataframe.index)] = item
        description = re.findall(r'Название: (.+) Заказчик:', ' '.join(info_file))[0]
        multiply_coefficient = sashQUA(description)
        canal_dataframe['description'] = description
    
        for item in corregs:
            cor = [item, 1, description]
            canal_dataframe.loc[len(canal_dataframe.index)] = cor
        canal_dataframe['quantity'] *= multiply_coefficient
        return canal_dataframe
    except:
        return pd.DataFrame()

def pdf_information_from_file(uploaded_file):
    all_text = ""
    # print(uploaded_file.name)
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if "ЛИСТ ТЕХНИЧЕСКОГО ПОДБОРА" in text:
                texts = text
                # st.write(texts)
                try:
                    texts = texts.split("\n")[3].split()[3:-2][0]
                except:
                    texts = texts.split("\n")
                    texts = [im for im in texts if "ЛИСТ ТЕХНИЧЕСКОГО ПОДБОРА" in im][0]
                    texts = texts.split()[3:-1][0]
            all_text += f"\n{text}"
    all_text = all_text.split("\n")
    all_text = [
        item.replace("Дополнительное оборудование ", "") for item in all_text if re.findall(r"(\w* Канал.*)", item) 
        or re.findall(r"(\w* КЛАБ.*)", item)
        or (re.findall(r"(\w* ВЕКТОР.*)", item) and "шт." in item)
        ]
    all_test = []
    for item in all_text:
        if not "Кассета фильтрующая" in item:
            all_test.append(item)
        else:
            if "шт." in item:
                all_test.append(item)
    correct_text = []
    for item in all_test:
        if "Гибкая вставка" in item or "Кассета фильтрующая" in item or "Каплеуловитель" in item or "Узел" in item or "Хомут" in item:
            correct_text.append(item)
        elif "водяной" in item or "фреоновый" in item or "обратный" in item or "воздушный" in item:
            correct_text.append(" ".join(item.split()[2:]))
        else:
            correct_text.append(" ".join(item.split()[1:]))
    correct_with_quantity = []
    for item in correct_text:
        if not "шт." in item:
            correct_with_quantity.append((item, 1, texts))
        else:
            quantity = int(re.findall(r"(\d*) шт.", item)[0])
            name = " ".join(item.split()[:-2])
            correct_with_quantity.append((name, quantity, texts))
    # coef = sashQUA(texts)
    coef = 1
    final = list(map(lambda x: (x[0], coef * x[1], x[2]), correct_with_quantity))
    dataframe = pd.DataFrame({
        "block": list(map(lambda x: x[0], final)),
        "quantity": list(map(lambda x: x[1], final)),
        "description": list(map(lambda x: x[2], final))}
    )
    # print(dataframe)
    return dataframe

def to_excel(df, HEADER=False, START=1):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, header=HEADER,startrow=START, startcol=START, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'})
    worksheet.set_column('B:B', None, format1)
    # worksheet.set_column('A:A', None, format1)
    for col_num, value in enumerate(df.columns):
        column_length = max(df[value].astype(str).map(len).max(), len(str(value)))
        worksheet.set_column(col_num+START, col_num+START, int(column_length * 1.2))
    writer.close()
    return output.getvalue()
