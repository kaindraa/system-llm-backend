from sqladmin import ModelView
from sqlalchemy.orm import Session
from wtforms import PasswordField
from wtforms.validators import DataRequired, Length, Optional
from uuid import UUID
from app.models.user import User
from app.models.model import Model
from app.models.prompt import Prompt
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.chat_session import ChatSession
from app.models.chat_config import ChatConfig
from app.core.security import get_password_hash


class UserAdmin(ModelView, model=User):
    """Admin view for User model"""

    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    # List view configuration
    column_list = [User.id, User.email, User.full_name, User.role, User.task, User.persona, User.created_at]
    column_searchable_list = [User.email, User.full_name]
    column_sortable_list = [User.email, User.full_name, User.role, User.created_at]
    column_default_sort = [(User.created_at, True)]  # Descending

    # Detail view configuration
    column_details_exclude_list = [User.password_hash, User.chat_sessions]
    # Removed User.password_hash from form_excluded_columns to allow password input
    form_excluded_columns = [User.created_at, User.updated_at, User.chat_sessions]

    # Permissions
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    # Display settings
    page_size = 50
    column_labels = {
        User.id: "ID",
        User.email: "Email",
        User.full_name: "Full Name",
        User.role: "Role",
        User.task: "Task",
        User.persona: "Persona",
        User.mission_objective: "Mission Objective",
        User.created_at: "Created",
        User.updated_at: "Updated",
    }

    # Form configuration
    form_args = {
        "password_hash": {
            "label": "Password",
            "validators": [DataRequired()],
            "description": "Enter password for the user",
        },
    }

    async def on_model_change(self, data: dict, model: User, is_create: bool, request) -> None:
        """
        Handle password hashing before saving user.
        This method is called before CREATE and UPDATE operations.
        """
        # Only hash password if it's provided and looks like plaintext (not already hashed)
        if "password_hash" in data and data["password_hash"]:
            password = data["password_hash"]
            # Check if password is not already hashed (bcrypt hashes start with $2a$, $2b$, or $2y$)
            if not (password.startswith("$2a$") or password.startswith("$2b$") or password.startswith("$2y$")):
                # Hash the password
                data["password_hash"] = get_password_hash(password)
        elif is_create:
            # If creating a new user and no password provided, raise error
            raise ValueError("Password is required when creating a new user")


class ModelAdmin(ModelView, model=Model):
    """Admin view for AI Model configuration"""

    name = "AI Model"
    name_plural = "AI Models"
    icon = "fa-solid fa-robot"

    # List view
    column_list = [Model.id, Model.name, Model.display_name, Model.provider, Model.created_at]
    column_searchable_list = [Model.name, Model.display_name, Model.provider]
    column_sortable_list = [Model.name, Model.display_name, Model.provider, Model.created_at]
    column_default_sort = [(Model.created_at, True)]

    # Detail view
    form_excluded_columns = [Model.created_at, Model.updated_at]

    # Permissions
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    page_size = 50
    column_labels = {
        Model.id: "ID",
        Model.name: "Name",
        Model.display_name: "Display Name",
        Model.provider: "Provider",
        Model.api_endpoint: "API Endpoint",
        Model.created_at: "Created",
        Model.updated_at: "Updated",
    }


class PromptAdmin(ModelView, model=Prompt):
    """Admin view for System Prompts"""

    name = "Prompt"
    name_plural = "Prompts"
    icon = "fa-solid fa-message"

    # List view
    column_list = [Prompt.id, Prompt.name, Prompt.description, Prompt.is_active, Prompt.created_at]
    column_searchable_list = [Prompt.name, Prompt.description]
    column_sortable_list = [Prompt.name, Prompt.is_active, Prompt.created_at]
    column_default_sort = [(Prompt.created_at, True)]

    # Detail view
    # Exclude created_by from form - it will be auto-set to current admin user
    form_excluded_columns = [Prompt.created_at, Prompt.updated_at, Prompt.created_by]

    # Permissions
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    page_size = 50
    column_labels = {
        Prompt.id: "ID",
        Prompt.name: "Name",
        Prompt.description: "Description",
        Prompt.content: "Content",
        Prompt.is_active: "Active",
        Prompt.created_by: "Created By",
        Prompt.created_at: "Created",
        Prompt.updated_at: "Updated",
    }

    async def on_model_change(self, data: dict, model: Prompt, is_create: bool, request) -> None:
        """
        Handle auto-setting created_by to current admin user before saving.
        This method is called before CREATE and UPDATE operations.
        """
        if is_create:
            # Get current admin user ID from session
            user_id = request.session.get("user_id")
            if user_id:
                # Convert user_id string to UUID
                data["created_by"] = UUID(user_id)
            else:
                # Fallback: raise error if no user_id in session
                raise ValueError("Cannot create prompt: No authenticated user found in session")


class DocumentAdmin(ModelView, model=Document):
    """Admin view for Documents"""

    name = "Document"
    name_plural = "Documents"
    icon = "fa-solid fa-file-pdf"

    # List view
    column_list = [
        Document.id,
        Document.filename,
        Document.user_id,
        Document.status,
        Document.file_size,
        Document.uploaded_at
    ]
    column_searchable_list = [Document.filename, Document.original_filename]
    column_sortable_list = [Document.filename, Document.status, Document.uploaded_at, Document.file_size]
    column_default_sort = [(Document.uploaded_at, True)]

    # Detail view
    form_excluded_columns = [Document.uploaded_at, Document.processed_at]

    # Permissions
    can_create = False  # Documents uploaded via API, not admin
    can_edit = True     # Can edit metadata
    can_delete = True   # Can delete documents
    can_view_details = True

    page_size = 50
    column_labels = {
        Document.id: "ID",
        Document.filename: "Filename",
        Document.original_filename: "Original Filename",
        Document.file_path: "File Path",
        Document.file_size: "File Size (bytes)",
        Document.mime_type: "MIME Type",
        Document.status: "Status",
        Document.user_id: "Uploaded By",
        Document.uploaded_at: "Uploaded At",
        Document.processed_at: "Processed At",
    }


class DocumentChunkAdmin(ModelView, model=DocumentChunk):
    """Admin view for Document Chunks (Read-only for monitoring)"""

    name = "Document Chunk"
    name_plural = "Document Chunks"
    icon = "fa-solid fa-cubes"

    # List view
    column_list = [
        DocumentChunk.id,
        DocumentChunk.document_id,
        DocumentChunk.chunk_index,
        DocumentChunk.page_number,
        DocumentChunk.created_at,
    ]
    column_searchable_list = [DocumentChunk.content]
    column_sortable_list = [
        DocumentChunk.document_id,
        DocumentChunk.chunk_index,
        DocumentChunk.page_number,
        DocumentChunk.created_at,
    ]
    column_default_sort = [(DocumentChunk.created_at, True)]

    # Detail view
    form_excluded_columns = [DocumentChunk.created_at, DocumentChunk.embedding]

    # Permissions - Read-only for monitoring
    can_create = False
    can_edit = False
    can_delete = True  # Allow cleanup
    can_view_details = True

    page_size = 100
    column_labels = {
        DocumentChunk.id: "ID",
        DocumentChunk.document_id: "Document",
        DocumentChunk.chunk_index: "Chunk Index",
        DocumentChunk.content: "Content",
        DocumentChunk.page_number: "Page Number",
        DocumentChunk.chunk_metadata: "Metadata (JSON)",
        DocumentChunk.created_at: "Created",
    }


class ChatSessionAdmin(ModelView, model=ChatSession):
    """Admin view for Chat Sessions (Read-only for research)"""

    name = "Chat Session"
    name_plural = "Chat Sessions"
    icon = "fa-solid fa-comments"

    # List view
    column_list = [
        ChatSession.id,
        ChatSession.user_id,
        ChatSession.model_id,
        ChatSession.status,
        ChatSession.prompt_general,
        ChatSession.task,
        ChatSession.persona,
        ChatSession.mission_objective,
        ChatSession.comprehension_level,
        ChatSession.started_at,
    ]
    column_searchable_list = [ChatSession.title]
    column_sortable_list = [
        ChatSession.user_id,
        ChatSession.model_id,
        ChatSession.status,
        ChatSession.started_at,
        ChatSession.ended_at,
    ]
    column_default_sort = [(ChatSession.started_at, True)]

    # Detail view
    form_excluded_columns = [ChatSession.started_at, ChatSession.ended_at, ChatSession.analyzed_at]

    # Permissions - Read-only for research
    can_create = False
    can_edit = True   # Allow updating metadata/status
    can_delete = True  # Allow cleanup
    can_view_details = True

    page_size = 50
    column_labels = {
        ChatSession.id: "ID",
        ChatSession.user_id: "User",
        ChatSession.model_id: "AI Model",
        ChatSession.prompt_id: "Prompt",
        ChatSession.title: "Title",
        ChatSession.messages: "Messages (JSON)",
        ChatSession.status: "Status",
        ChatSession.prompt_general: "General Prompt",
        ChatSession.task: "Task",
        ChatSession.persona: "Persona",
        ChatSession.mission_objective: "Mission/Objective",
        ChatSession.total_messages: "Total Messages",
        ChatSession.comprehension_level: "Comprehension",
        ChatSession.summary: "Summary",
        ChatSession.started_at: "Started At",
        ChatSession.ended_at: "Ended At",
        ChatSession.analyzed_at: "Analyzed At",
    }


class ChatConfigAdmin(ModelView, model=ChatConfig):
    """Admin view for Chat Configuration (System Settings)"""

    name = "Chat Config"
    name_plural = "Chat Config"
    icon = "fa-solid fa-gears"

    # List view
    column_list = [
        ChatConfig.id,
        ChatConfig.prompt_general,
        ChatConfig.default_top_k,
        ChatConfig.max_top_k,
        ChatConfig.similarity_threshold,
        ChatConfig.tool_calling_enabled,
        ChatConfig.updated_at,
    ]
    column_searchable_list = []  # No searchable columns
    column_sortable_list = [ChatConfig.updated_at]
    column_default_sort = [(ChatConfig.updated_at, True)]

    # Detail view - exclude timestamp (auto-updated)
    form_excluded_columns = [ChatConfig.updated_at]

    # Permissions - Full control for system settings
    can_create = False  # Singleton table, only one config allowed
    can_edit = True     # Allow editing all settings
    can_delete = False  # Cannot delete system config
    can_view_details = True

    page_size = 1  # Only one config record
    column_labels = {
        ChatConfig.id: "Config ID",
        ChatConfig.prompt_general: "General System Prompt",
        ChatConfig.default_top_k: "Default Top-K Results",
        ChatConfig.max_top_k: "Maximum Top-K Results",
        ChatConfig.similarity_threshold: "Similarity Threshold (0-1)",
        ChatConfig.tool_calling_max_iterations: "Tool Calling Max Iterations",
        ChatConfig.tool_calling_enabled: "Tool Calling Enabled",
        ChatConfig.include_rag_instruction: "Include RAG Instruction in Prompts",
        ChatConfig.updated_at: "Last Updated",
    }

    # Form configuration with descriptions
    form_args = {
        "prompt_general": {
            "label": "General System Prompt",
            "description": "System-wide general prompt that applies to all chat sessions",
        },
        "default_top_k": {
            "label": "Default Top-K Results",
            "description": "Default number of document chunks to return in semantic search (1-100)",
        },
        "max_top_k": {
            "label": "Maximum Top-K Results",
            "description": "Maximum allowed number of results per search request (1-100)",
        },
        "similarity_threshold": {
            "label": "Similarity Threshold",
            "description": "Minimum similarity score required for results (0.0 to 1.0, where 1.0 is most similar)",
        },
        "tool_calling_max_iterations": {
            "label": "Tool Calling Max Iterations",
            "description": "Maximum number of times the LLM can call tools in a single message (1-100)",
        },
        "tool_calling_enabled": {
            "label": "Enable Tool Calling",
            "description": "Allow LLM to use semantic_search tool during chat",
        },
        "include_rag_instruction": {
            "label": "Include RAG Instruction",
            "description": "Add RAG instruction to system prompt to guide LLM to use tools",
        },
    }
