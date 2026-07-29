from functools import lru_cache
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_classic.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.prompts import PromptTemplate
import torch
import re
from transformers import AutoTokenizer, AutoModelForCausalLM


model_name = "mistralai/Mistral-7B-Instruct-v0.2"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
)


def generate_text(prompt: str, max_new_tokens: int = 256, num_return_sequences: int = 1) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            num_return_sequences=num_return_sequences,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=0.7,
        )
    return [tokenizer.decode(output, skip_special_tokens=True) for output in outputs][0]


@lru_cache(maxsize=4)
def build_vectordb(pdf_path: str):
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    text_splitter = CharacterTextSplitter(chunk_size=1200, chunk_overlap=80)
    chunks = text_splitter.split_documents(documents)

    embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embedding = HuggingFaceEmbeddings(model_name=embedding_model_name)
    return FAISS.from_documents(chunks, embedding)


full_name_schema = ResponseSchema(
    name="full_name",
    description="The full legal name of the applicant.",
)
email_schema = ResponseSchema(
    name="email",
    description="The email address of the applicant.",
)
education_schema = ResponseSchema(
    name="education",
    description="A list of the education that the applicant completed with degree, institution and year of graduation.",
)
skills_schema = ResponseSchema(
    name="skills",
    description="A list of all skills stated in applicant resume.",
)
experience_schema = ResponseSchema(
    name="experience",
    description="A list of the experiences that the applicant had including role, company and the period of employment.",
)

response_schemas = [
    full_name_schema,
    email_schema,
    education_schema,
    skills_schema,
    experience_schema,
]

output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = output_parser.get_format_instructions()

resume_extraction_template = """You are a senior human resouses manager that extracts qualifications out of applicants' resumes.

Extract all qualifications as following:
full name
email address
education containing degree, the institution from which the dgree got issued and the year of graduation 
skills containing all major skills the applicant have
experience containing role name, company name and the period of employment.


Respond ONLY in JSON format as follows:
{format_instructions}

Example Input:
"
John Smith – john.smith@email.com
Education: B.Sc. Computer Science, MIT, 2020
Skills: Python, Machine Learning, Data Analysis
Experience:
- Software Engineer at Google (2020–2023)
- Data Scientist at OpenAI (2023–Present)
"

Now extract from the following input:
"{user_input}"
"""


def ask_question(query: str, vectordb) -> str:
    docs = vectordb.similarity_search(query, k=2)
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = f"""You are a helpful assistant. Use the following context to answer the question. Context: {context} Question: {query} Answer:"""

    result = generate_text(prompt, max_new_tokens=256)
    return result.strip()


def extract_json_block(text: str) -> str:
    pattern = r'```json\s*(.*?)\s*```'
    matches = re.findall(pattern, text, re.DOTALL)
    if not matches:
        return text
    return f"```json\n{matches[-1]}\n```"


def run_resume_analysis(pdf_path: str, user_input: str):
    vectordb = build_vectordb(pdf_path)

    prompt = PromptTemplate(
        template=resume_extraction_template,
        input_variables=["user_input", "format_instructions"],
    ).format(user_input=user_input, format_instructions=format_instructions)

    answer = ask_question(prompt, vectordb=vectordb)
    json_text = extract_json_block(answer)
    output_data = output_parser.parse(json_text)
    return output_data

__all__ = ["run_resume_analysis", "build_vectordb", "generate_text"]
