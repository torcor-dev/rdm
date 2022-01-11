create or replace function reddit_meta_subreddit_trg()
returns trigger
as $$
declare
    subreddit_name varchar;
begin
    if not exists(select name from subreddit where name=new.subreddit) then
        insert into subreddit(name) values(new.subreddit);
    end if;
    return new;
end; 
$$
language plpgsql;

drop trigger if exists new_subreddits on reddit_meta;
create trigger new_subreddits
    before insert or update on reddit_meta
    for each row
    execute function reddit_meta_subreddit_trg();
