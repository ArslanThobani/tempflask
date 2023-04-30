from googlesearch import search
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ['apikey']
bo = None

class BusinessObject:
   def __init__(self, 
      companyName, industry, 
      product=None,
      businessModel=None,
      productLine=None,
      audience=None,
      differentiateFactor=None,
      goal=None,
      challenges=None,
      budget=None,
      implAIBefore=None,
      goalAI=None,
      limitInfra=None):
      self.companyName = companyName
      self.industry = industry
      self.product=product,
      self.businessModel=businessModel,
      self.productLine=productLine,
      self.audience=audience,
      self.differentiateFactor=differentiateFactor,
      self.goal=goal,
      self.challenges=challenges,
      self.budget=budget,
      self.implAIBefore=implAIBefore,
      self.goalAI=goalAI
      self.limitInfra=limitInfra

def extract_text_from_url(url):
   req = Request(
      url=url, 
      headers={'User-Agent': 'Mozilla/6.0'}
   )
   html = urlopen(req).read()
   clean_text = ' '.join(BeautifulSoup(html, "html.parser").stripped_strings)
   # soup = BeautifulSoup(html, features="html.parser")
   # for script in soup(["script", "style"]):
   #    script.extract()
   # text = soup.get_text()
   # lines = (line.strip() for line in text.splitlines())
   # chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
   # text = ' '.join(chunk for chunk in chunks if chunk)
   return clean_text

def get_prompt_from_bo(bo, google_summary):
   prompt = "You are an AI use case ideation machine. You must evaluate all the background information provided to you about a business, and suggest 5 possible AI use cases, where they can implement AI. Below is the background information:"
   prompt += f"Our business {bo.companyName} belongs to the {bo.industry}. "
   prompt += f"Our business model is based on {bo.businessModel}. " if bo.businessModel is not None else ""  
   prompt += f"We offer {bo.product} ." if bo.product is not None else ""
   prompt += f"Our customers are {bo.audience}. " if bo.audience is not None else ""
   prompt += f"What differentiates our business from our competitors is that {bo.differentiateFactor}. " if bo.differentiateFactor is not None else ""
   prompt += f"Our major challenge is {bo.challenges}. " if bo.challenges is not None else ""
   prompt += f"{bo.implAIBefore} implemented AI solutions before in our business. " if bo.implAIBefore is not None else ""
   prompt += f"Our company's mission is {bo.goal}. " if bo.goal is not None else ""
   prompt += f"The outcome we wish to achieve with AI adoption {bo.goalAI}. " if bo.goalAI is not None else ""
   prompt += f"IT or infrastructure limitations that need to be considered for AI implementation: {bo.limitInfra}. " if bo.limitInfra is not None else ""
   return prompt


def request_gpt_response(prompt):
   r = openai.Completion.create(
      model="text-davinci-003",
      prompt=prompt,
      temperature=0.1,
      max_tokens=2000,
      frequency_penalty=1.0,
      presence_penalty=0.0
   )
   return r.choices[0].text

@app.route('/')
def hello_world():
   return 'Hello World'

def get_uses_cases_google_search(bo):
   query = f"Artifical Intelligence in {bo.industry} business"

   texts = []
   for idx, url in enumerate(search(query, lang="en", tld="com", num=2, stop=4, pause=2)):
      try:
         text = extract_text_from_url(url)[3100:-1500]
         print(f"len of text#{idx}: {len(text)}")
         texts.append(text)
         if len(texts) == 1:
            break
      except:
         print("Couldn't retrieve website content") 
   
   string_text = ". ".join(texts)
   string_text = f"Read the following texts and make a summary of specific use cases where I can use AI in my business in {bo.industry}"
   summary = request_gpt_response(string_text)
   return summary

@app.route('/get_use_cases_chat_gpt', methods=['POST'])
def get_use_cases_chat_gpt():
   content = request.get_json(silent=True)
   global bo
   if bo is None:
      bo = BusinessObject(
            companyName=content.get('companyName'),
            industry=content.get('industry'),
            product=content.get('product'),
            businessModel=content.get('businessModel'),
            productLine=content.get('productLine'),
            audience=content.get('audience'),
            differentiateFactor=content.get('differentiateFactor'),
            goal=content.get('goal'),
            challenges=content.get('challenges'),
            budget=content.get('budget'),
            implAIBefore=content.get('implAIBefore'),
            goalAI=content.get('goalAI'),
            limitInfra=content.get('limitInfra')
      )
   google_summary = get_uses_cases_google_search(bo)
   prompt = get_prompt_from_bo(bo, google_summary)
   chat_gpt_summary = request_gpt_response(prompt)

   use_case_list = chat_gpt_summary.split('\n')
   use_case_list = [uc for uc in use_case_list if len(uc) > 0]
   bo.use_case_list = use_case_list

   print(bo.use_case_list)

   # return get_costs_risks()

   return use_case_list
   
   # print(f"Summary from google: {google_summary}")
   # print(f"Prompt is: {prompt}")
   # return request_gpt_response(f"Output use cases of AI using bullet points from these 2 texts: 1) {google_summary}. 2) {chat_gpt_summary}")
   # prompt += f"You might use the following text to include and compile all examples and use cases of ingerating AI into our business case. {google_summary}"
   

@app.route('/get_costs_risks')
def get_costs_risks():
   global bo
   prompt = "Below is the output you came up with when I asked you to behave like an AI use case ideation assistant:"
   prompt += ". ".join(bo.use_case_list)
   prompt += """ Your role is now different. Come up with responses to the following questions for every use case: 
   1. What are the potential costs and risks of implementing each of the above use cases?
   2. Do an evaluation of how the implementation of the AI use case would create business value for the company
   3. Recommend data sources that will be required to implement this use case and where to look for these sources or specific examples """
   answers_list = request_gpt_response(prompt).split("\n\n")
   answers_list = [ans for ans in answers_list if len(ans) > 0]
   return answers_list


# if __name__ == '__main__':
#    app.run(port=8000, debug=True)
