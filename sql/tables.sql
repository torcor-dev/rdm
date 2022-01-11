create table media (
    id serial primary key,
    file_name varchar(255) unique,
    format varchar(10),
    height integer,
    width integer,
    aspect_ratio numeric,
    size numeric,
    media_type varchar(40)
);

create table video (
    id serial primary key,
    media_id integer,
    frame_rate varchar(100),
    duration varchar(255),
    constraint video_media_fk foreign key(media_id) 
        references media(id) on delete cascade
);

create table subreddit (
    name varchar(255) primary key
);

create table tag (
    name varchar(255) primary key
);

--drop table if exists subreddit_tag;
create table subreddit_tag (
    tag_name varchar(255),
    subreddit_name varchar(255),
    constraint subreddit_tag_pk primary key(tag_name, subreddit_name),
    constraint subreddit_tag_subreddit_fk foreign key(subreddit_name)
        references subreddit(name) on delete cascade,
    constraint subreddit_tag_tag_fk foreign key(tag_name)
        references tag(name) on delete cascade
);

create table file_tag (
    tag_name varchar(255),
    file_name varchar(255),
    constraint file_tag_pk primary key(tag_name, file_name)
);
    
create table reddit_meta (
    id serial primary key,
    author varchar(255),
    created numeric,
    reddit_id varchar(25) unique,
    permalink text,
    score integer,
    subreddit varchar(255),
    title text,
    url text,
    constraint reddit_meta_subreddit_fk foreign key(subreddit) references subreddit(name)
);

create table post_link (
    media_id integer,
    reddit_meta_id integer,
    constraint post_link_pk primary key(media_id, reddit_meta_id),
    constraint post_link_media_fk foreign key(media_id)
        references media(id) on delete cascade,
    constraint post_link_reddit_meta_fk foreign key(reddit_meta_id)
        references reddit_meta(id) on delete cascade
);

create index media_file_name_idx on media(file_name);
create index reddit_meta_reddit_id_idx on reddit_meta(reddit_id);
