from langgraph.graph import StateGraph, END
from agents.state import ProcureAIState
from agents.planner_agent import planner_agent
from agents.icp_agent import icp_agent
from agents.web_search_agent import web_search_agent
from agents.company_validation_agent import company_validation_agent
from agents.decision_maker_agent import decision_maker_agent
from agents.contact_enrichment_agent import contact_enrichment_agent
from agents.recommendation_agent import recommendation_agent

def create_discovery_graph():
    """
    Creates the Customer Discovery Agent Pipeline.
    Defines the order in which agents run.
    """
    graph = StateGraph(ProcureAIState)

    # Add all agents as nodes
    graph.add_node("planner_node", planner_agent)
    graph.add_node("icp_node", icp_agent)
    graph.add_node("web_search_node", web_search_agent)
    graph.add_node("validation_node", company_validation_agent)
    graph.add_node("decision_maker_node", decision_maker_agent)
    graph.add_node("enrichment_node", contact_enrichment_agent)
    graph.add_node("recommendation_node", recommendation_agent)

    # Define the flow
    graph.set_entry_point("planner_node")
    graph.add_edge("planner_node", "icp_node")
    graph.add_edge("icp_node", "web_search_node")
    graph.add_edge("web_search_node", "validation_node")
    graph.add_edge("validation_node", "decision_maker_node")
    graph.add_edge("decision_maker_node", "enrichment_node")
    graph.add_edge("enrichment_node", "recommendation_node")
    graph.add_edge("recommendation_node", END)

    return graph.compile()

# Single instance used everywhere
discovery_graph = create_discovery_graph()