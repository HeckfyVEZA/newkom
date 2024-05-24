import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
from help_defs import information_from_file, to_excel

files = st.file_uploader("Upload your file", type=['docx'], accept_multiple_files=True)

def descr_merge(df, block):
    return ', '.join(df[df['block'] == block['block']]['description'])

if files:
    full_dataframe = pd.concat([information_from_file(file) for file in files]).reset_index(drop=True)
    gr = st.checkbox('Сгруппировать?', value=False)
    f_data = full_dataframe.copy()
    if gr:
        f_data = f_data.groupby(['block']).sum().reset_index()[['block', 'quantity']]
        f_data['description'] = f_data.apply(lambda x:descr_merge(full_dataframe, x), axis=1)
    st.dataframe(f_data, use_container_width=True)
    for_check = full_dataframe.copy()
    for_check['check'] = "<u>" + for_check['block'] + '</u> : <b>' + for_check['quantity'].astype(str) + "</b> шт."
    pivot_check = for_check.pivot_table(index='description', values=['check'], aggfunc=lambda x: ',<br>'.join(x)).reset_index()
    html_text = "<br>".join(["<b>" + pivot_check.iloc[i, 0] + "</b> :<br>" + pivot_check.iloc[i, 1] + "<br>" for i in range(pivot_check.shape[0])])
    with st.expander("📋 Список всех блоков"):
        st.markdown(html_text.replace("*", "\*"), unsafe_allow_html=True)
    st.download_button(label='💾 Скачать файл для проверки', data=html_text, file_name='проверка.html')
    st.download_button(label='💾 Скачать файл для выгрузки в КП', data=to_excel(f_data), file_name='для кп.xls')