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
    st.download_button(label='💾 Скачать файл для выгрузки в КП',data=to_excel(f_data), file_name= 'для кп.xls')