suppressPackageStartupMessages({
  library(ggplot2)
  library(patchwork)
  library(dplyr)
  library(tidyr)
  library(readr)
  library(svglite)
  library(ragg)
})

palette_contract <- c(
  neutral_dark = "#272727",
  neutral_mid = "#767676",
  neutral_light = "#D8D8D8",
  signal_blue = "#3182BD",
  signal_teal = "#33B5A5",
  accent_red = "#D24B40",
  accent_orange = "#E28E2C"
)

theme_nature_contract <- function(base_size = 6.5, base_family = "Arial") {
  theme_classic(base_size = base_size, base_family = base_family) +
    theme(
      axis.line = element_line(linewidth = 0.35, colour = "black"),
      axis.ticks = element_line(linewidth = 0.35, colour = "black"),
      axis.title = element_text(size = base_size),
      axis.text = element_text(size = base_size - 0.5),
      legend.title = element_text(size = base_size - 0.3),
      legend.text = element_text(size = base_size - 0.7),
      strip.text = element_text(size = base_size - 0.3, face = "bold"),
      plot.title = element_text(size = base_size + 0.5, face = "bold"),
      panel.grid = element_blank()
    )
}

theme_set(theme_nature_contract())

save_pub_r <- function(plot, filename, width_mm = 183, height_mm = 120, dpi = 600) {
  w <- width_mm / 25.4
  h <- height_mm / 25.4

  svglite::svglite(paste0(filename, ".svg"), width = w, height = h)
  print(plot)
  dev.off()

  grDevices::cairo_pdf(paste0(filename, ".pdf"), width = w, height = h, family = "Arial")
  print(plot)
  dev.off()

  ragg::agg_tiff(paste0(filename, ".tiff"), width = w, height = h, units = "in", res = dpi)
  print(plot)
  dev.off()
}

require_non_empty <- function(df, file) {
  if (nrow(df) == 0) {
    stop(paste0("No real experiment rows found in ", file,
                ". Fill the CSV with measured data before rendering Chapter 5 figures."),
         call. = FALSE)
  }
  invisible(df)
}

script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
script_path <- if (length(script_arg) > 0) {
  sub("^--file=", "", script_arg[[1]])
} else {
  "chapter5_plot_templates.R"
}
script_path <- normalizePath(script_path, mustWork = FALSE)
data_dir <- file.path(dirname(script_path), "chapter5_data")
out_dir <- file.path(dirname(data_dir), "chapter5_figures")
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

read_required <- function(name) {
  path <- file.path(data_dir, name)
  if (!file.exists(path)) {
    stop(paste0("Missing required data file: ", path), call. = FALSE)
  }
  require_non_empty(readr::read_csv(path, show_col_types = FALSE), path)
}

plot_search_space_quality <- function() {
  df <- read_required("search_space_summary.csv")

  action_df <- df %>%
    select(space, benchmark, dtype, shape_id, direct_count, adapt_count, fallback_count, reject_count) %>%
    pivot_longer(ends_with("_count"), names_to = "action", values_to = "count")

  p_actions <- ggplot(action_df, aes(x = space, y = count, fill = action)) +
    geom_col(width = 0.72) +
    facet_grid(dtype ~ benchmark, scales = "free_y") +
    scale_fill_manual(values = c(
      direct_count = palette_contract["signal_blue"],
      adapt_count = palette_contract["signal_teal"],
      fallback_count = palette_contract["accent_orange"],
      reject_count = palette_contract["accent_red"]
    )) +
    labs(x = NULL, y = "Candidates", fill = "Action")

  p_valid <- ggplot(df, aes(x = space, y = valid_rate, colour = space)) +
    geom_point(size = 1.5) +
    facet_grid(dtype ~ benchmark) +
    scale_colour_manual(values = c(
      "kernel-aware" = palette_contract["signal_blue"],
      "generic" = palette_contract["neutral_mid"]
    )) +
    labs(x = NULL, y = "Valid candidate rate")

  fig <- (p_actions | p_valid) +
    plot_annotation(tag_levels = "a") &
    theme(plot.tag = element_text(size = 8, face = "bold"))

  save_pub_r(fig, file.path(out_dir, "fig5_search_space_quality"))
}

plot_convergence <- function() {
  df <- read_required("convergence_trace.csv")

  p <- ggplot(df, aes(x = budget_step, y = best_latency_ms, colour = space, group = run_id)) +
    geom_line(linewidth = 0.35) +
    geom_point(size = 0.8) +
    facet_grid(dtype ~ benchmark, scales = "free_y") +
    scale_colour_manual(values = c(
      "kernel-aware" = palette_contract["signal_blue"],
      "generic" = palette_contract["neutral_mid"]
    )) +
    labs(x = "Evaluation budget", y = "Best-so-far latency (ms)", colour = "Space")

  save_pub_r(p, file.path(out_dir, "fig5_convergence"))
}

plot_replacement_and_ablation <- function() {
  repl <- read_required("replacement_success.csv")
  ablation <- read_required("ablation_summary.csv")

  p_repl <- ggplot(repl, aes(x = space, y = replacement_success_rate, colour = space)) +
    geom_point(size = 1.5) +
    facet_grid(dtype ~ benchmark) +
    scale_colour_manual(values = c(
      "kernel-aware" = palette_contract["signal_blue"],
      "generic" = palette_contract["neutral_mid"]
    )) +
    labs(x = NULL, y = "Replacement success rate", colour = "Space")

  p_abl <- ggplot(ablation, aes(x = ablation, y = valid_rate)) +
    geom_col(width = 0.72, fill = palette_contract["signal_teal"]) +
    facet_grid(dtype ~ benchmark) +
    coord_flip() +
    labs(x = NULL, y = "Valid candidate rate")

  fig <- (p_repl | p_abl) +
    plot_annotation(tag_levels = "a") &
    theme(plot.tag = element_text(size = 8, face = "bold"))

  save_pub_r(fig, file.path(out_dir, "fig5_replacement_ablation"))
}

plot_search_space_quality()
plot_convergence()
plot_replacement_and_ablation()
