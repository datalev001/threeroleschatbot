# streamlit run c:\streamlit_app\openai_mistral_v1.py
# pip install openai==0.28.0
#user_request = " How to deal with inflation if economy is slow? give me the best answer"
# how to work efficiently if your boss ask you to do something you believe is 100% unworkable and your boss is not listening to others' opinion?

import streamlit as st
import openai  # Add this import statement
import os
from ctransformers import AutoModelForCausalLM

openai.api_type = "azure"
# Azure OpenAI on your own data is only supported by the 2023-08-01-preview API version
openai.api_version = "2023-06-01-preview"
# Azure OpenAI setup
openai.api_base = "https://******"
openai.api_key = "*********"
deployment_id = "gpt4"

# here I use openai==0.28.0
print(openai.__version__)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi, how can I help you?"}]
    st.session_state.conversation = ""
    st.session_state.qa = []
    st.session_state.questions = ""
    st.session_state.roles = ['host']
    
# Function to send a message using the Mistral model
def send_message_mistral(user_request, action, openai_response_final=""):
    llm = AutoModelForCausalLM.from_pretrained("Mistral-7B-Instruct-v0.1-GGUF", model_file="mistral-7b-instruct-v0.1.Q4_K_M.gguf", model_type="mistral", gpu_layers=0)

    if action == "Answer":
        prompt = f"(request) Provide an answer for the following question in less than 120 English words: {user_request}"
    elif action == "Evaluate":
        prompt = f"(request) Based on the following question and OpenAI's answer, provide an evaluation and focuss on the drawbacks of the answer in less than 100 English words. Question: {user_request}, OpenAI's Answer: {openai_response_final}"

    print('mistral_prompt:', prompt)
    mistral_response = ""  # Placeholder for the Mistral API response
    for text in llm(prompt, stream=True):
        #print(text, end="", flush=True)
        mistral_response = mistral_response + text

    print('mistral_response:', mistral_response)

    return mistral_response


# Function to send a message using the OpenAI model
def send_message_openai(user_request, action, mistral_response_final=""):

   notice = '. Note, do not randomly fabricate unless you more than 50% know, otherwise say I do not know, also your answer should be clear, brief, do not repeat the question'
   your_knowledge = ' Use the general knowledge in business and economics '

   start_messages = [
       {"role": "system", "content": "You are a good helper assistant for answering business or economics questions"},
       {"role": "user", "content": "Can you answer some questions on behalf expert"},
       {"role": "assistant", "content": "Sure, I can"},
       {"role": "user", "content": notice},
       {"role": "assistant", "content": "Sure, I will follow this instruction"},
       {"role": "user", "content": "Here is our conversation history including the questions from user and answers from assistant, please do not answer them, only use the information to answer the most recent question"},
       {"role": "assistant", "content": "Yes, I will use the conversation history information to keep chatting"}
   ]

   if action == "Answer":
       end_messages = [{"role": "user", "content": f'Now, {your_knowledge} please answer the most recent question using less than 120 English words: {user_request}, please provide the answer using the full knowledge in our conversational history'}]
   elif action == "Evaluate":
       end_messages = [{"role": "user", "content": f'Evaluate this response: {mistral_response_final} for the question: {user_request}'}]

   message_lst = start_messages + end_messages
   
   print('openai_prompt:', end_messages)

   response = openai.ChatCompletion.create(
       deployment_id=deployment_id,
       temperature=0.7,
       max_tokens=150,
       messages=message_lst
   )

   bot_response = response['choices'][0]['message']['content'].strip()
   
   print('openai_response:', bot_response)
   
   return bot_response    

# Layout for buttons
col1, col2 = st.columns(2)

# New chat button with unique key
if col1.button("New chat", key="new_chat_button"):
    st.session_state.messages = [{"role": "assistant", "content": "Hi, how can I help you?"}]
    st.session_state.conversation = ""
    st.session_state.qa = []
    st.session_state.questions = ""
    st.session_state.discuss_clicked = False
    st.session_state.roles = ['host']

# Sidebar for role and action selection
selected_role = st.sidebar.radio("Select Role:", ("OpenAI", "Mistral", "Interactive"))
selected_action = st.sidebar.radio("Select Action:", ("Answer", "Evaluate"))

# Add "Discuss" button with a unique key
discuss_button_key = "discuss_button_key"
discuss_button_disabled = (st.session_state.conversation == "")

if col2.button("Chat", key=discuss_button_key, disabled=discuss_button_disabled):
    if st.session_state.conversation:
        st.session_state.discuss_clicked = True

        # Get the last user's message from the conversation
        L_role = len(st.session_state.roles)
        user_question = st.session_state.questions
        last_message = ""
                
        if (selected_role != st.session_state.roles[L_role-1]) and (L_role> 1):
            last_message = st.session_state.qa[-1][1]
        else:
            selected_action = "Answer"
            
                        
        with st.chat_message("assistant"):
            answer = ""
            if selected_role == "OpenAI":
                answer = send_message_openai(user_request=user_question, action=selected_action, mistral_response_final = last_message)
                st.session_state.roles.append("OpenAI")
            elif selected_role == "Mistral":
                answer = send_message_mistral(user_request = user_question, action=selected_action, openai_response_final = last_message)
                st.session_state.roles.append("Mistral")

            # Displaying the answer
            st.markdown(f'<span style="color: black;">{answer}</span>', unsafe_allow_html=True)
            
            prompt = '<br>' + user_question.replace('\n', '<br>')    
            answer = '<br>' + answer
            if selected_role == "OpenAI":
                q_and_a = (
                    f'<span style="color: black; background-color: white;"><b>[host]:</b>&nbsp; {prompt}</span> <br>'
                    f'<span style="color: blue; background-color: white;"><b>[{selected_role}][{selected_action}]:</b>&nbsp; {answer}</span>'
                )
            else:
                q_and_a = (
                    f'<span style="color: black; background-color: white;"><b>[host]:</b>&nbsp; {prompt}</span> <br>'
                    f'<span style="color: red; background-color: white;"><b>[{selected_role}][{selected_action}]:</b>&nbsp; {answer}</span>'
                )

            ll = '<br><br>'
            st.session_state.conversation = st.session_state.conversation + "<br>" + ll + q_and_a
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.session_state.qa.append([prompt, answer])

if prompt := st.chat_input("Write here.."):
    st.chat_message("user").markdown(prompt.replace(';', '\n'))
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.questions = prompt
    
    with st.chat_message("assistant"):
        answer = ""
        selected_action = "Answer"
        
        if selected_role == "OpenAI":
            answer = send_message_openai(user_request=prompt, action=selected_action)
            st.session_state.roles.append("OpenAI")
        elif selected_role == "Mistral":
            answer = send_message_mistral(user_request=prompt, action=selected_action)
            st.session_state.roles.append("Mistral")

        # Displaying the answer
        st.markdown(f'<span style="color: black;">{answer}</span>', unsafe_allow_html=True)
         
    prompt = '<br>' + prompt.replace('\n', '<br>')    
    answer = '<br>' + answer
    
    if selected_role == "OpenAI":
        q_and_a = (
         f'<span style="color: black; background-color: white;"><b>[host]:</b>&nbsp; {prompt}</span> <br>'
         f'<span style="color: blue; background-color: white;"><b>[{selected_role}][{selected_action}]:</b>&nbsp; {answer}</span>'
        )
    else:
        q_and_a = (
         f'<span style="color: black; background-color: white;"><b>[host]:</b>&nbsp; {prompt}</span> <br>'
         f'<span style="color: red; background-color: white;"><b>[{selected_role}][{selected_action}]:</b>&nbsp; {answer}</span>'
        )
        
     
    ll = '<br><br>'
    st.session_state.conversation = st.session_state.conversation + "<br>" + ll + q_and_a
    st.session_state.messages.append({"role": "assistant", "content": answer})    
    st.session_state.qa.append([prompt, answer])    
     
   

table_placeholder = st.sidebar.empty()

message_ini = ""
table_content = f"<div style='text-align: left; color: #3f3e3e42; font-size: 25px;'>{message_ini}</div>"
table_placeholder.markdown(table_content, unsafe_allow_html=True)

readonly_styles = """
    <style>
        .readonly-text-area {
            color: black;
            background-color: white;
            font-size: 14px;
            font-style: italic;
            border: 1px solid #ccc;
            padding: 8px;
            overflow-y: auto;
        }
    </style>
"""

if st.session_state.conversation != "":
    st.markdown(readonly_styles + f'<div class="readonly-text-area">{st.session_state.conversation}</div>', unsafe_allow_html=True)


