--
-- PostgreSQL database dump
--

\restrict FFdAuCuM8VhQ0xPAxDuMYzfEf9O9uIiyO9uWTmh6YQiPn0xtzJGJRxLc1Z5PwRl

-- Dumped from database version 15.15
-- Dumped by pg_dump version 15.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: comprehensionlevel; Type: TYPE; Schema: public; Owner: llm_user
--

CREATE TYPE public.comprehensionlevel AS ENUM (
    'BASIC',
    'INTERMEDIATE',
    'ADVANCED'
);


ALTER TYPE public.comprehensionlevel OWNER TO llm_user;

--
-- Name: documentstatus; Type: TYPE; Schema: public; Owner: llm_user
--

CREATE TYPE public.documentstatus AS ENUM (
    'UPLOADED',
    'PROCESSING',
    'PROCESSED',
    'FAILED'
);


ALTER TYPE public.documentstatus OWNER TO llm_user;

--
-- Name: sessionstatus; Type: TYPE; Schema: public; Owner: llm_user
--

CREATE TYPE public.sessionstatus AS ENUM (
    'active',
    'analyzed'
);


ALTER TYPE public.sessionstatus OWNER TO llm_user;

--
-- Name: taskstatus; Type: TYPE; Schema: public; Owner: llm_user
--

CREATE TYPE public.taskstatus AS ENUM (
    'PENDING',
    'PROCESSING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);


ALTER TYPE public.taskstatus OWNER TO llm_user;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: llm_user
--

CREATE TYPE public.userrole AS ENUM (
    'STUDENT',
    'ADMIN'
);


ALTER TYPE public.userrole OWNER TO llm_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: llm_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO llm_user;

--
-- Name: chat_config; Type: TABLE; Schema: public; Owner: llm_user
--

CREATE TABLE public.chat_config (
    id integer DEFAULT 1 NOT NULL,
    default_top_k integer DEFAULT 5 NOT NULL,
    max_top_k integer DEFAULT 10 NOT NULL,
    similarity_threshold double precision DEFAULT '0.7'::double precision NOT NULL,
    tool_calling_max_iterations integer DEFAULT 10 NOT NULL,
    tool_calling_enabled integer DEFAULT 1 NOT NULL,
    include_rag_instruction integer DEFAULT 1 NOT NULL,
    updated_at timestamp with time zone DEFAULT now(),
    prompt_general text,
    prompt_analysis text,
    prompt_refine text
);


ALTER TABLE public.chat_config OWNER TO llm_user;

--
-- Name: COLUMN chat_config.prompt_refine; Type: COMMENT; Schema: public; Owner: llm_user
--

COMMENT ON COLUMN public.chat_config.prompt_refine IS 'Prompt template for LLM to refine/clarify student questions';


--
-- Name: chat_session; Type: TABLE; Schema: public; Owner: llm_user
--

CREATE TABLE public.chat_session (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    prompt_id uuid,
    model_id uuid NOT NULL,
    title character varying(255),
    messages jsonb NOT NULL,
    status character varying(50),
    comprehension_level character varying(50),
    summary text,
    started_at timestamp with time zone DEFAULT now(),
    ended_at timestamp with time zone,
    analyzed_at timestamp with time zone,
    total_messages integer,
    prompt_general text,
    task text,
    persona text,
    mission_objective text,
    interaction_messages jsonb,
    real_messages jsonb
);


ALTER TABLE public.chat_session OWNER TO llm_user;

--
-- Name: document; Type: TABLE; Schema: public; Owner: llm_user
--

CREATE TABLE public.document (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    filename character varying(255) NOT NULL,
    original_filename character varying(255) NOT NULL,
    file_path character varying(500) NOT NULL,
    file_size bigint NOT NULL,
    mime_type character varying(100),
    status public.documentstatus,
    uploaded_at timestamp with time zone DEFAULT now(),
    processed_at timestamp with time zone,
    content text
);


ALTER TABLE public.document OWNER TO llm_user;

--
-- Name: model; Type: TABLE; Schema: public; Owner: llm_user
--

CREATE TABLE public.model (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    display_name character varying(255) NOT NULL,
    provider character varying(100),
    api_endpoint character varying(500),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    "order" integer DEFAULT 0
);


ALTER TABLE public.model OWNER TO llm_user;

--
-- Name: prompt; Type: TABLE; Schema: public; Owner: llm_user
--

CREATE TABLE public.prompt (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    content text NOT NULL,
    description text,
    is_active boolean,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.prompt OWNER TO llm_user;

--
-- Name: user; Type: TABLE; Schema: public; Owner: llm_user
--

CREATE TABLE public."user" (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(255) NOT NULL,
    role public.userrole NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    task text,
    persona text,
    mission_objective text
);


ALTER TABLE public."user" OWNER TO llm_user;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: llm_user
--

COPY public.alembic_version (version_num) FROM stdin;
p1q2r3s4t5u6
\.


--
-- Data for Name: chat_config; Type: TABLE DATA; Schema: public; Owner: llm_user
--

COPY public.chat_config (id, default_top_k, max_top_k, similarity_threshold, tool_calling_max_iterations, tool_calling_enabled, include_rag_instruction, updated_at, prompt_general, prompt_analysis, prompt_refine) FROM stdin;
1	5	10	0.25	5	1	1	2025-11-22 09:14:21.141208+00	You are a helpful learning assistant with access to two powerful tools:\r\n\r\n## Available Tools:\r\n\r\n1. **refine_prompt** - Use this tool to clarify or improve unclear/ambiguous student questions\r\n   - When: The student's question is vague, incomplete, or could be interpreted multiple ways\r\n   - Result: Returns a more specific and clear version of the question for better search results\r\n   - Example: "gimana loop?" → "Jelaskan apa itu loop dan perbedaan antara for dan while loop"\r\n\r\n2. **semantic_search** - Use this tool to find relevant documents and information from the knowledge base\r\n   - When: You need to retrieve specific information to answer the student's question\r\n   - Input: A clear search query (ideally refined from refine_prompt if needed)\r\n   - Result: Returns relevant document chunks with page numbers and similarity scores\r\n\r\n## Recommended Workflow:\r\n\r\n1. **Read the student's question carefully**\r\n   - If it's unclear/ambiguous → Use refine_prompt to clarify first\r\n   - If it's already clear → Proceed to semantic_search\r\n\r\n2. **Search the knowledge base**\r\n   - Use the refined (or original if clear) question to search documents\r\n   - Pass it as the query parameter to semantic_search\r\n\r\n3. **Synthesize and answer**\r\n   - Combine the search results with your knowledge\r\n   - Cite the document sources when appropriate\r\n   - Provide comprehensive answer that addresses the student's actual need\r\n\r\n## Key Principles:\r\n- Always prioritize understanding what the student actually needs\r\n- Use refine_prompt strategically - only when needed for clarity\r\n- Reference document sources to build trust and allow students to explore further\r\n- If search returns no results, try alternative search terms or explain what information is available	Analisis percakapan chat berikut dan berikan respons dalam format JSON:\r\n\r\nRINGKASAN: Tulis 1-2 paragraf ringkasan tentang topik apa yang dibahas dan poin-poin penting yang dipelajari.\r\n\r\nTINGKAT PEMAHAMAN: Nilai tingkat pemahaman siswa sebagai LOW, MEDIUM, atau HIGH berdasarkan:\r\n- Kualitas pertanyaan yang diajukan\r\n- Kejelasan pemahaman yang ditunjukkan\r\n- Tingkat keterlibatan dan interaksi\r\n\r\nKembalikan HANYA dalam format JSON berikut (tanpa teks lain):\r\n{\r\n  "summary": "ringkasan 1-2 paragraf di sini",\r\n  "comprehension_level": "LOW|MEDIUM|HIGH"\r\n}	Tingkatkan prompt student agar lebih jelas dan selalu mulai dengan kata RAJA
\.


--
-- Data for Name: chat_session; Type: TABLE DATA; Schema: public; Owner: llm_user
--

COPY public.chat_session (id, user_id, prompt_id, model_id, title, messages, status, comprehension_level, summary, started_at, ended_at, analyzed_at, total_messages, prompt_general, task, persona, mission_objective, interaction_messages, real_messages) FROM stdin;
\.


--
-- Data for Name: document; Type: TABLE DATA; Schema: public; Owner: llm_user
--

COPY public.document (id, user_id, filename, original_filename, file_path, file_size, mime_type, status, uploaded_at, processed_at, content) FROM stdin;
159d1944-e4cf-4ece-a26f-1eed25d25341	f6d6db1d-e162-4f7b-9f0e-892a9d128cc7	842563bf-8647-42f8-8704-49690fee2b95	Software-Engineering-9th-Edition-by-Ian-Sommerville.pdf	gs://system-llm-storage/uploads/842563bf-8647-42f8-8704-49690fee2b95.pdf	5397464	application/pdf	PROCESSED	2025-11-14 09:47:17.755123+00	2025-11-14 10:39:36.910824+00	\N
cf4226d2-0c6a-452d-bd57-23df56a9204b	f6d6db1d-e162-4f7b-9f0e-892a9d128cc7	af5020f2-593d-4e2f-8560-f36bcea3236a	Software Engineering - Roger S Pressman [5th edition].pdf	gs://system-llm-storage/uploads/af5020f2-593d-4e2f-8560-f36bcea3236a.pdf	6986228	application/pdf	PROCESSING	2025-11-14 10:24:51.821016+00	\N	\N
34dc2341-3cde-4404-8584-14a57e29e0db	f6d6db1d-e162-4f7b-9f0e-892a9d128cc7	8bc7e5dc-6310-45fc-b503-5ba146ebba12	Forum WA2 (2).pdf	gs://system-llm-storage/uploads/8bc7e5dc-6310-45fc-b503-5ba146ebba12.pdf	62297	application/pdf	UPLOADED	2025-12-01 06:25:09.594791+00	\N	\N
df21d720-665d-4075-bda0-f75b1ba0436f	f6d6db1d-e162-4f7b-9f0e-892a9d128cc7	cc0be48c-f6d8-4062-9ac5-ad01fdba800b	NAMA PANJAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANG.pdf	gs://system-llm-storage/uploads/cc0be48c-f6d8-4062-9ac5-ad01fdba800b.pdf	62297	application/pdf	UPLOADED	2025-12-01 06:26:19.353249+00	\N	\N
1327a5fd-a6ff-4fdb-a15f-d99b1410206d	f6d6db1d-e162-4f7b-9f0e-892a9d128cc7	d4327599-5819-40a3-95b1-2215c4390107	Project-Management-Institute-A-Guide-to-the-Project-Management-Body-of-Knowledge-PMBOK-R-Guide-PMBOK®️-Guide-Project.pdf	gs://system-llm-storage/uploads/d4327599-5819-40a3-95b1-2215c4390107.pdf	20680390	application/pdf	UPLOADED	2025-12-07 09:08:15.605259+00	\N	\N
d5138382-928d-41d4-b574-63f1f8ce7c56	550e8400-e29b-41d4-a716-446655440000	5f34648f-acfb-4680-abfa-2026a241d047	Tugas_Individu_4___Pemrosesan_Bahasa_Lisan_2025_2026.pdf	storage/uploads/5f34648f-acfb-4680-abfa-2026a241d047.pdf	530630	application/pdf	UPLOADED	2025-12-07 11:26:51.640637+00	\N	\N
\.


--
-- Data for Name: model; Type: TABLE DATA; Schema: public; Owner: llm_user
--

COPY public.model (id, name, display_name, provider, api_endpoint, created_at, updated_at, "order") FROM stdin;
efa04cd0-553f-4cb5-9130-3f365d4e411e	gpt-4.1-nano	GPT-4.1 Nano	OPENAI	https://api.openai.com/v1/chat/completions	2025-12-07 11:16:57.983617+00	2025-12-07 11:16:57.983617+00	0
ac371fee-4ff1-4944-9492-2f396d7117c2	claude-haiku-4-5	Claude Haiku 4.5	ANTHROPIC	https://api.anthropic.com/v1/messages	2025-12-07 11:17:46.48074+00	2025-12-07 11:17:46.48074+00	1
ad37656e-0029-42f9-ba27-6732ac3215d2	gemini-2.5-flash	Gemini 2.5 Flash	GOOGLE	https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent	2025-12-07 11:17:57.41536+00	2025-12-07 11:17:57.41536+00	2
e4c9a5af-ccb5-40b9-8c7d-378fa4d4a5e5	meta-llama/llama-3.1-8b-instruct	Llama 3.1 8B (OpenRouter)	openrouter	https://openrouter.ai/api/v1	2025-12-07 11:17:57.41536+00	2025-12-07 11:17:57.41536+00	10
0af9ac43-19d0-4b50-af03-49c4fc269ac4	qwen/qwen-2.5-7b-instruct	Qwen 2.5 7B (OpenRouter)	openrouter	https://openrouter.ai/api/v1	2025-12-07 11:17:57.41536+00	2025-12-07 11:17:57.41536+00	11
16e618ff-2726-438c-812a-690535c4079b	microsoft/phi-3-medium-128k-instruct	Phi-3 Medium (OpenRouter)	openrouter	https://openrouter.ai/api/v1	2025-12-07 11:17:57.41536+00	2025-12-07 11:17:57.41536+00	12
\.


--
-- Data for Name: prompt; Type: TABLE DATA; Schema: public; Owner: llm_user
--

COPY public.prompt (id, name, content, description, is_active, created_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: llm_user
--

COPY public."user" (id, email, password_hash, full_name, role, created_at, updated_at, task, persona, mission_objective) FROM stdin;
550e8400-e29b-41d4-a716-446655440000	admin@example.com	$2b$12$IkU9Y0apDIuhML2RHOjWKOLEVTPYngGbKvDrVZxv3YCYDQxEpX/p.	Admin User	ADMIN	2025-12-07 11:10:41.174249+00	2025-12-07 11:10:41.174249+00	\N	\N	\N
df68adb8-fa90-401a-804d-d7deec00e6c8	student@example.com	$2b$12$sjTtBT6NRz0IW/5vZz/kI.FxX5IDcK2c3S23fZOI7/8eZ/L0YILMS	First Student	STUDENT	2025-12-07 11:14:36.094639+00	2025-12-07 11:14:36.094639+00	\N	\N	\N
\.


--
-- PostgreSQL database dump complete
--

\unrestrict FFdAuCuM8VhQ0xPAxDuMYzfEf9O9uIiyO9uWTmh6YQiPn0xtzJGJRxLc1Z5PwRl

