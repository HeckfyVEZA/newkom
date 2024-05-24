import pandas as pd
from docx2txt import process
import re
import io
from itertools import dropwhile, takewhile
from data_freq import frequency_manager

def sashQUA(main_system_name:str, the_mask = r'\d?[A-Za-zА-Яа-яЁё]\D?\D?\D?\D?\S?\S?\S?\S?\d{1,}[А-Яа-яЁё]?'):
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

def information_from_file(uploaded_file):
    canal_dataframe = pd.DataFrame()
    info_file = [item for item in process(uploaded_file).split('\n') if item]
    infofreq = list(map(lambda item: re.findall(r'Эл.двиг: Ny=(\d{1,3},?\d{1,3}) кВт; Uпит=~?(\d{1,3}) ?В; Iпот=(\d{1,3},?\d{1,3}) A', item), info_file))
    infofreq = [list(map(lambda x: float(x.replace(',', '.')), item[0])) for item in list(infofreq) if item]
    freg_must_be = list(map(lambda item: re.findall(r"Регулятор оборотов двигателя .+ вентилятора: (.{2,3})", item), info_file))
    freg_must_be = [item for item in list(freg_must_be) if item]
    infofreq = [infofreq[i] + [freg_must_be[i][0]] for i in range(len(infofreq))]
    corregs = []
    for item in infofreq:
        p, v, c, must = item
        if must == 'да':
            corregs += [frequency_manager.query('voltage==@v and current>@c and power >= @p').iloc[0]['name']]
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
    canal_dataframe['quantity'] *= multiply_coefficient
    for item in corregs:
        cor = [item, 1, description]
        canal_dataframe.loc[len(canal_dataframe.index)] = cor
    return canal_dataframe

def to_excel(df, HEADER=False, START=1):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    pd.DataFrame(df).to_excel(writer, index=False, header=HEADER,startrow=START, startcol=START, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'})
    worksheet.set_column('A:A', None, format1)
    writer.close()
    return output.getvalue()
