source("code/00_load_dependencies.R")

indeed_df <- read.csv("data/output/Indeed_scrape_daily_compiliation.csv")
#boros_df <- read.csv("data/output/Indeed_scrape_boros_compiliation.csv")
#indeed_test_df <- read.csv("~/Desktop/Indeed_scrape_daily_compiliation.csv")
#bk_df <- read.csv("~/Desktop/Indeed_scrape_bk_compiliation.csv")
#test <- read.csv("~/Desktop/test.csv")
#google_df <- read.csv("~/Desktop/google-jobs-cronjob.csv")


look <- (boros_df %>%
    select(-date_scraped,-location,-post_date) %>%
    do.call(paste0,.)) %in%
  (indeed_df %>%
     filter(strptime(date_scraped, "%m/%d/%Y %H:%M:%S") >= "2023-09-05 14:00:00 EDT") %>%
    select(-date_scraped,-post_date) %>%
    do.call(paste0, .)) %>% which()

boros_df %>%
  slice(look) %>%
  View()

### Prepping data

## NOTES: Cannot think of a way to remove duplicates without some (pot) large assumptions.
##.       1) Post dates can be the same if they have multiple positions available.
##.          The chances of this may also depend on industry.
##        2) Some only have Last Activity by Employer. This makes it more difficult to
##           differentiate job postings.
##        3) Indeed may show repeats simply by how job postings are generated whenever
##           you click "Next". Unsure about how their system works - if it's one seed or
##           whatever. To add to the confusion, they 'eliminate' jobs similar once you hit
##           1500 jobs.

indeed_df <- indeed_df %>%
  mutate(salary_provided = ifelse(grepl("Estimated",salary_snippet) | is.na(salary_snippet),0,1), # Create new column for if salary provided
         is_salary_range = ifelse(grepl("-",salary_snippet) & !is.na(salary_snippet),1,0), # Check if salary is a range
         salary_type = ifelse(!is.na(salary_snippet),str_extract(salary_snippet,"[\\w]+$"),NA)
         ) %>%
  rowwise() %>%
  mutate(lower_salary = ifelse(is_salary_range,parse_number(str_extract_all(salary_snippet,"\\$([0-9,.]+)")[[1]][1]),NA), # Grab lower and upper salaries
         upper_salary = ifelse(is_salary_range, parse_number(str_extract_all(salary_snippet,"\\$([0-9,.]+)")[[1]][2]),NA),
         salary_diff = ifelse(salary_provided & is_salary_range, upper_salary - lower_salary, NA),
         salary_ratio = ifelse(!is.na(salary_diff),upper_salary/lower_salary,NA)
         )

## NOTES: I'm treating "Estimated..." and "NA"s the same as the salary was both not provided.

### EDA
# Table of salaries provided
table(indeed_df$salary_provided)/nrow(indeed_df)

# How many posts are posted per hour?
indeed_df %>%
  group_by(date_scraped) %>%
  summarise(count = n()) %>%
  slice(-1) %>%
  ggplot(.,aes(x=date_scraped, y = count, group = 1)) +
  geom_line() +
  theme_nycc() +
  scale_x_discrete(breaks = function(x){x[c(TRUE, FALSE, FALSE, FALSE, FALSE, FALSE)]})+
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) 

# Particular day most postings are done normalized by week total
indeed_df %>%
  mutate(weekday_posted = wday(strptime(date_scraped, "%m/%d/%Y %H:%M:%S"),label = TRUE),
         week_posted = week(strptime(date_scraped, "%m/%d/%Y %H:%M:%S"))) %>%
  group_by(weekday_posted, week_posted) %>%
  summarise(count = n()) %>%
  ungroup() %>%
  group_by(week_posted) %>%
  mutate(weekday_normalized = count/sum(count)) %>% View()
  group_by(weekday_posted) %>%
  summarise(wday_sum = sum(weekday_normalized)) %>%
  ggplot(.,aes(x=weekday_posted, y = wday_sum, group = 1)) +
  geom_line() +
  geom_point() +
  theme_nycc() +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1))

# Particular hour most postings are done normalized by day total
indeed_df %>%
  mutate(hour_posted = hour(strptime(date_scraped, "%m/%d/%Y %H:%M:%S"))) %>%
  group_by(hour_posted) %>%
  summarise(count = n()) %>%
  ggplot(.,aes(x=hour_posted, y = count, group = 1)) +
  geom_line() +
  geom_point() +
  theme_nycc() +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1))

# Annual salary difference distribution
# Histogram overlaid with kernel density curve
ggplot(indeed_df %>%
         filter(
                salary_provided == 1), aes(x=salary_ratio)) + 
  geom_histogram(aes(y=..density..),
                 colour="black", fill="white") +
  geom_density(alpha=.2, fill="#FF6666")

# What are these jobs that have high ratios?
job_titles_to_exclude = c("On-Site Healthcare Pre-Screening")
salary_year_diff_1 <- indeed_df %>%
  filter(salary_ratio > 2,
         salary_provided == 1,
         !grepl( job_titles_to_exclude, job_title, fixed = TRUE))

salary_year_diff_1 %>%
  distinct(.keep_all = TRUE) %>%
  select(job_title, company_name, salary_snippet, salary_diff, salary_ratio) %>%
  arrange(desc(salary_ratio)) %>%
  gt() %>%
  gt_theme_nytimes() %>%
  tab_header(
    title = "Indeed Jobs",
    subtitle = glue::glue("With salary ranges greater than their lower bound")
  ) %>%
  fmt_currency(columns = salary_diff) %>%
  fmt_percent(columns = salary_ratio)

