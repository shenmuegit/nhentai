-- public.artist definition

-- Drop table

-- DROP TABLE public.artist;

CREATE TABLE public.artist (
	id SERIAL PRIMARY KEY,
	"name" varchar NULL
);
CREATE UNIQUE INDEX artists_name_idx ON public.artist USING btree (name);


-- public.book definition

-- Drop table

-- DROP TABLE public.book;

CREATE TABLE public.book (
	id SERIAL PRIMARY KEY,
	"name" varchar NULL,
	"language" varchar NULL,
	url varchar NULL,
	page int4 NULL,
	"path" varchar NULL
);


-- public.book_artist definition

-- Drop table

-- DROP TABLE public.book_artist;

CREATE TABLE public.book_artist (
	id SERIAL PRIMARY KEY,
	book_id int8 NULL,
	artist_id int8 NULL
);
CREATE INDEX book_artist_book_id_idx ON public.book_artist USING btree (book_id, artist_id);


-- public.book_tag definition

-- Drop table

-- DROP TABLE public.book_tag;

CREATE TABLE public.book_tag (
	id SERIAL PRIMARY KEY,
	book_id int8 NULL,
	tag_id int8 NULL
);
CREATE INDEX book_tag_book_id_idx ON public.book_tag USING btree (book_id, tag_id);


-- public.tag definition

-- Drop table

-- DROP TABLE public.tag;

CREATE TABLE public.tag (
	id SERIAL PRIMARY KEY,
	"name" varchar NULL
);
CREATE UNIQUE INDEX tag_name_idx ON public.tag USING btree (name);