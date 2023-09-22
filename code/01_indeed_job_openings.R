source("code/00_load_dependencies.R")

indeed_jp_df <- read_csv("data/input/metro_job_postings_us.csv") %>%
  clean_names() %>%
  filter(cbsa_title == "New York-Newark-Jersey City, NY-NJ-PA") %>%
  mutate(percent = (indeed_job_postings_index - 100) )

plot_a <- ggplot(indeed_jp_df , aes(x=date,y=percent)) +
    geom_point(color= pal_nycc("cool")[7], size =0.5) +
    geom_smooth(se=F, span=0.25, color = pal_nycc("cool")[7]) +
    scale_x_date(date_labels = "%m-%y", breaks = "2 months") +
    #theme_nycc()
    theme_minimal() +
    ggtitle("Feb 20 Index % Change",
          "New York-Newark-Jersey City, NY-NJ-PA")



month_jp <- read_csv("data/input/metros_data_2023-09-15.csv") %>%
  clean_names()

plot_b <- ggplot(month_jp, aes(x=date,
                               y=seasonally_adjusted_percentage)) +
  geom_point(color= pal_nycc("cool")[7], size=0.5) +
  geom_smooth(se=F, span=0.25, color = pal_nycc("cool")[7]) +
  scale_x_date(date_labels = "%m-%y", breaks = "2 months") +
  theme_minimal() +
  ggtitle("Month-over-Month % Change",
          "New York-Newark-Jersey City, NY-NJ-PA")
  #theme_nycc()
