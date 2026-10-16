import json
from pathlib import Path 
from typing import TypedDict 
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph , START , END 
from pypdf import PdfReader 

from fields import Fields , reader_pdf 

BASE  = Path(__file__).parent
load_dotenv(BASE /'.env')

MAX_RETRIES = 3 


model = init_chat_model(
    model = 'openai/gpt-oss-120b',
    model_provider = 'groq',

)

PROMPT = """Extract invoice fields from this bill text.

Return exactly these fields:
- bill_no: the invoice number (the # near the top)
- date: the bill date
- customer_name: the person or company the bill is for
- total: the grand total amount as a number, no currency symbol, no commas

Bill text:
{text}
"""

class State(TypedDict):
    path : str 
    attempt : int 
    text : str 
    error : str 
    row : dict 

def read_pdf(state :State) -> dict:
    try:
        return { 'text': reader_pdf(PdfReader(state['path'])) , 'error' :''}
    except Exception as e:
        return {'text':'' , 'error': f'read failed: {e}'}
    

def extract_fields(state : State) -> dict:
    try:
        response = model.with_structured_output(Fields).invoke(
            PROMPT.format(text = state['text'])
        )
        return {'row': {'file': Path(state['path']).name , **response.model_dump(), 'error': ''}}
    except Exception as e :
        return {'error': f'extract failed : {e}' , 'attempt' : state['attempt'] +1 }

def finalize(state : State ) -> dict:
    if state['error']:
        return {'row' :{'file': Path(state['path']).name , 'error': state['error']}}
    return {} # no change in state 



def route(state:State) -> str:
    if state['error'] and state['attempt'] < MAX_RETRIES:
        return 'retry'
    return 'done' 

builder = StateGraph(State)

builder.add_node('read_pdf' , read_pdf)
builder.add_node('extract_fields' , extract_fields)
builder.add_node('finalize' , finalize)

builder.add_edge(START ,  'read_pdf')
builder.add_edge('read_pdf','extract_fields')
builder.add_conditional_edges('extract_fields', route  , {'retry': 'extract_fields' , 'done': 'finalize'})
builder.add_edge('finalize', END)

graph = builder.compile()

rows = []
for pdf in sorted((BASE / 'in').glob('*.pdf')):
    state = graph.invoke({'path': str(pdf) ,'attempt' : 0 ,'text': '' , 'error' :'' ,'row':{} })
    rows.append(state['row'])

(BASE / 'out').mkdir(exist_ok = True)
with open(BASE / 'out' / 'result.json' , 'w', encoding = 'utf-8' ) as f :
    json.dump(rows , f , indent = 2 )

print(json.dumps(rows,indent = 2))
