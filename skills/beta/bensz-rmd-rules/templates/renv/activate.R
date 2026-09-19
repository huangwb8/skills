# Minimal activation entry copied to renv/activate.R for new projects.
# renv::init() normally replaces this with its generated activation script.
project_root <- normalizePath(".", winslash = "/", mustWork = TRUE)
if (!requireNamespace("renv", quietly = TRUE)) {
  stop("This project requires renv. Run renv::init() once during initialization.")
}
renv::load(project = project_root)
