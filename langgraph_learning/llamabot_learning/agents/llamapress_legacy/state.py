from typing import Optional, TypedDict


##LEGACY for LlamaPress v1. This is a custom state object for our legacy LlamaPress v1 agent.
class LlamaPressMessage(TypedDict):
    user_message: str
    system_prompt: Optional[str] = None
    message_type: Optional[str] = None
    context: Optional[str] = None
    selected_element: Optional[str] = None
    file_contents: Optional[str] = None
    web_page_id: Optional[str] = None
    previous_messages: Optional[list[dict]] = None
    # forbidding extra we handle the default shape as options
    webPageId: Optional[str] = None
    message: Optional[str] = None
    selectedElement: Optional[str] = None
    wordpress_api_encoded_token: Optional[str] = None
    user_llamapress_api_token: Optional[str] = None
    llamapress_origin_domain: Optional[str] = None
    llamabot_agent_name: Optional[str] = None
    javascript_console_errors: Optional[str] = None
