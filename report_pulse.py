import streamlit as st
import os
os.environ["OPENAI_API_KEY"] = st.secrets["openai_api_key"]
from pathlib import Path
from streamlit_chat import message
from llama_index_utils import ReportPulseAssistent
import json
from prompts import REPORT_PROMPT

st.set_page_config(
    page_title="Report Pulse",
    page_icon="favicon.ico",
)

path = os.path.dirname(__file__)

# Load translations from JSON file
with open(path+"/Assets/translations.json") as f:
    transl = json.load(f)

# Trick to preserve the state of your widgets across pages
for k, v in st.session_state.items():
    st.session_state[k] = v 
##


styl = f"""
<style>
    .stTextInput {{
      position: fixed;
      bottom: 3rem;
      z-index: 2;
    }}
    #root > div:nth-child(1) > div.withScreencast > div > div > div > section > div.block-container.css-1y4p8pa {{
        display: flex !important;
        float:left;
        overflow-y: auto;
        flex-direction: column-reverse;
    }}
</style>
"""
st.markdown(styl, unsafe_allow_html=True)


# Add the language selection dropdown    
if 'lang_tmp' not in st.session_state:
    st.session_state['lang_tmp'] = 'English'

if 'lang_changed' not in st.session_state:
    st.session_state['lang_changed'] = False

if 'lang_select' in st.session_state:
    #st.sidebar.markdown("<h3 style='text-align: center; color: black;'>{}</h3>".format(transl[st.session_state['lang_select']]["language_selection"]), unsafe_allow_html=True)
    lang = st.sidebar.selectbox(transl[st.session_state['lang_select']]["language_selection"], options=list(transl.keys()), key='lang_select')
else:
    #st.sidebar.markdown("<h3 style='text-align: center; color: black;'>{}</h3>".format(transl[st.session_state['lang_tmp']]["language_selection"]), unsafe_allow_html=True)
    lang = st.sidebar.selectbox(transl[st.session_state['lang_tmp']]["language_selection"], options=list(transl.keys()), key='lang_select')

if lang != st.session_state['lang_tmp']:
    st.session_state['lang_tmp'] = lang
    st.session_state['lang_changed'] = True
    st.experimental_rerun()
else:
    st.session_state['lang_changed'] = False

st.title(transl[lang]["title"])

file_uploaded = st.file_uploader(label=transl[lang]["title"])

styl = f"""
<style>
    .stTextInput {{
      position: fixed;
      bottom: 3rem;
    }}
</style>
"""
st.markdown(styl, unsafe_allow_html=True)

if file_uploaded is not None:
    
    def display_messages():
        
        for i, (msg, is_user) in enumerate(st.session_state["messages"]):
            #message( msg, is_user=is_user, key=str(i), allow_html = True )
            message( msg, is_user=is_user, key=str(i) )
        st.session_state["thinking_spinner"] = st.empty()
    
    def process_input():
        if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
            user_text = st.session_state["user_input"].strip()
            with st.session_state["thinking_spinner"], st.spinner(transl[lang]["thinking"]):
                agent_text = generate_response(user_text)

            st.session_state["messages"].append((user_text, True))
            st.session_state["messages"].append((agent_text, False))
            st.session_state["user_input"] = ""
            
    # Storing the chat
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    def showmessage(output):
        st.session_state["messages"].append((output, False))

    def validate_value_in_range(record):
        parameter_value = float(record['Result'])
        biological_range = record['Biological Ref Range'].split(' ')[0]
        biological_low_range, biological_high_range  = [float(val) for val in biological_range.split('-')]
        if parameter_value < biological_low_range:
            record['variation'] = str(format(parameter_value - biological_low_range,".2f"))
        elif parameter_value > biological_high_range:
            record['variation'] = str(format(parameter_value - biological_high_range,".2f"))
        return record


    def get_relevant_report(reports):
        # resports data format is expected to be a list of json object
        abnormal_data_numeric = []
        string_data = []
        for record in reports:
            if record.get("Result", "unknown") != "unknown":
                try:
                    new_record = validate_value_in_range(record)
                    abnormal_data_numeric.append(new_record)
                except Exception as e:
                    # if here means the value is string type
                    #st.success(e)
                    string_data.append(record)
        new_report = {
            "numeric": abnormal_data_numeric,
            "string": string_data
        }
        return new_report 

    def get_st_col_metric(report):
        
        reports_temp = get_relevant_report(report)['numeric']
        #st.success(json.dumps(reports_temp))
        #st.success(json.dumps(report))
        reports = []
        for rec in reports_temp: 
            if "variation" in rec:
                reports.append(rec)
                #reports.remove(rec)

        #st.success(json.dumps(reports))
        # pick the first 5 reports
        reports = reports[:5]
        cols = st.columns(len(reports))
        for col, record in zip(cols, reports):
            col.metric(record["Parameter"], record["Result"], str(record["variation"]))
            
    def upload_file(uploadedFile):
        
        # Save uploaded file to 'content' folder.
        save_folder = '/app/reportsData/'
        save_path = Path(save_folder, uploadedFile.name)
        
        with open(save_path, mode='wb') as w:
            w.write(uploadedFile.getvalue())

        with st.spinner(transl[lang]["scan"]):
            return ReportPulseAssistent(save_folder,lang=lang)
        
    reportPulseAgent = upload_file(file_uploaded)
    with st.spinner(transl[lang]["gen_summary"]):    
        r_response = reportPulseAgent.get_next_message(lang=lang,prompt_type='summary')
    
    st.sidebar.markdown(r_response)
    st.markdown("""---""")
    st.sidebar.markdown(""" <br /><br />
                      :rotating_light: **{}** :rotating_light: <br />
                            {}
                            """.format(transl[lang]['caution'], transl[lang]['caution_message']), 
                            unsafe_allow_html=True
    )
    with st.spinner(transl[lang]["gen_report"]): 
        try:
            reports_response = reportPulseAgent.get_next_message(REPORT_PROMPT,lang=lang,prompt_type='report')
            #st.success(json.dumps(reports_response))
            reports = json.loads(reports_response)
            #st.success(json.dumps(reports))
            st.sidebar.markdown(get_st_col_metric(reports))
        except Exception as e:
            pass

    def generate_response(user_query):
        response = reportPulseAgent.get_next_message(user_query, lang=lang,prompt_type='other')
        return response

    # We will get the user's input by calling the get_text function

    st.text_input(transl[lang]['ask_question'],key="user_input", on_change=process_input)
    display_messages()