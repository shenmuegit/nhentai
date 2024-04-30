-- public.artist definition

-- Drop table

-- DROP TABLE public.artist;

CREATE TABLE public.artist (
	id int8 NOT NULL,
	"name" varchar NULL,
	CONSTRAINT artists_pk PRIMARY KEY (id)
);
CREATE UNIQUE INDEX artists_name_idx ON public.artist USING btree (name);


-- public.book definition

-- Drop table

-- DROP TABLE public.book;

CREATE TABLE public.book (
	id int8 NOT NULL,
	"name" varchar NULL,
	"language" varchar NULL,
	url varchar NULL,
	page int4 NULL,
	"path" varchar NULL,
	CONSTRAINT book_pk PRIMARY KEY (id)
);


-- public.book_artist definition

-- Drop table

-- DROP TABLE public.book_artist;

CREATE TABLE public.book_artist (
	id int8 NOT NULL,
	book_id int8 NULL,
	artist_id int8 NULL,
	CONSTRAINT book_artist_pk PRIMARY KEY (id)
);
CREATE INDEX book_artist_book_id_idx ON public.book_artist USING btree (book_id, artist_id);


-- public.book_tag definition

-- Drop table

-- DROP TABLE public.book_tag;

CREATE TABLE public.book_tag (
	id int8 NULL,
	book_id int8 NULL,
	tag_id int8 NULL
);
CREATE INDEX book_tag_book_id_idx ON public.book_tag USING btree (book_id, tag_id);


-- public.tag definition

-- Drop table

-- DROP TABLE public.tag;

CREATE TABLE public.tag (
	id int8 NOT NULL,
	"name" varchar NULL,
	CONSTRAINT tag_pk PRIMARY KEY (id)
);
CREATE UNIQUE INDEX tag_name_idx ON public.tag USING btree (name);