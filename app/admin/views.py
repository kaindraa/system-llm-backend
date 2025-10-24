from sqladmin import ModelView
from app.models.user import User
from app.models.model import Model
from app.models.prompt import Prompt
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.chat_session import ChatSession


class UserAdmin(ModelView, model=User):
    """Admin view for User model"""

    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    # List view configuration
    column_list = [User.id, User.email, User.full_name, User.role, User.created_at]
    column_searchable_list = [User.email, User.full_name]
    column_sortable_list = [User.email, User.full_name, User.role, User.created_at]
    column_default_sort = [(User.created_at, True)]  # Descending

    # Detail view configuration
    column_details_exclude_list = [User.password_hash]
    form_excluded_columns = [User.password_hash, User.created_at, User.updated_at]

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
        User.created_at: "Created",
        User.updated_at: "Updated",
    }


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
    form_excluded_columns = [Prompt.created_at, Prompt.updated_at]

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
        ChatSession.total_user_msg: "User Messages",
        ChatSession.total_assistant_msg: "AI Responses",
        ChatSession.comprehension_level: "Comprehension",
        ChatSession.summary: "Summary",
        ChatSession.started_at: "Started At",
        ChatSession.ended_at: "Ended At",
        ChatSession.analyzed_at: "Analyzed At",
    }
