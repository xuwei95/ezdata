from langchain.chains import RetrievalQA
from web_apps.rag.utils import get_vector_index
from web_apps.llm.llm_utils import get_llm
vector_index = get_vector_index()
print(vector_index)
res = vector_index.search('限流')
print(res)
retriever = vector_index.get_retriever()  # search_kwargs={'filter': {'t3': "22222"}}
# query = "获取A股东方财富实时股票信息使用哪个api？返回格式是什么样的"
query = "限流"
llm = get_llm()
qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever)
result = qa_chain({"query": query})
print(result)