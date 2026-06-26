from langgraph.graph import StateGraph, END
from agents.state import ProcureAIState
from agents.planner_agent import planner_agent
from agents.document_agent import document_agent
from agents.comparison_agent import comparison_agent
from agents.risk_agent import risk_agent
from agents.negotiation_agent import negotiation_agent
from agents.recommendation_agent import recommendation_agent

def create_procurement_graph():
    graph = StateGraph(ProcureAIState)

    # Nodes renamed to avoid conflict with state keys
    graph.add_node("planner_node", planner_agent)
    graph.add_node("document_node", document_agent)
    graph.add_node("comparison_node", comparison_agent)
    graph.add_node("risk_node", risk_agent)
    graph.add_node("negotiation_node", negotiation_agent)
    graph.add_node("recommendation_node", recommendation_agent)

    graph.set_entry_point("planner_node")
    graph.add_edge("planner_node", "document_node")
    graph.add_edge("document_node", "comparison_node")
    graph.add_edge("comparison_node", "risk_node")
    graph.add_edge("risk_node", "negotiation_node")
    graph.add_edge("negotiation_node", "recommendation_node")
    graph.add_edge("recommendation_node", END)

    return graph.compile()

procurement_graph = create_procurement_graph()