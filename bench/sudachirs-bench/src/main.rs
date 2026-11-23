use std::io::BufRead;
use std::io::Write;
use std::path::PathBuf;

use sudachi::analysis::stateful_tokenizer::StatefulTokenizer;
use sudachi::config::Config;
use sudachi::dic::dictionary::JapaneseDictionary;
use sudachi::dic::subset::InfoSubset;
use sudachi::prelude::*;

/// The split mode from the first argument (A, B or C; C when it is left out),
/// and the name of the series it gives, as run_all.sh and stats.py use it.
fn split_mode() -> (Mode, &'static str) {
    match std::env::args().nth(1).as_deref() {
        Some("A") => (Mode::A, "sudachi.rs-a"),
        Some("B") => (Mode::B, "sudachi.rs-b"),
        Some("C") | None => (Mode::C, "sudachi.rs-c"),
        Some(other) => panic!("unknown split mode {other:?}: use A, B or C"),
    }
}

fn main() {
    let (mode, series) = split_mode();
    let config = Config::new(
        None,
        None,
        Some(PathBuf::from(
            "./bench/sudachi-bench/sudachi-dictionary-20261015/system_core.dic",
        )),
    )
    .unwrap();
    let dict = JapaneseDictionary::from_cfg(&config).unwrap();
    let mut tokenizer = StatefulTokenizer::new(&dict, mode);
    // The subset always keeps what the mode needs (the split information of
    // modes A and B), see StatefulTokenizer::set_subset.
    tokenizer.set_subset(InfoSubset::empty());
    let mut morphemes = MorphemeList::empty(&dict);
    let lines: Vec<_> = std::io::stdin()
        .lock()
        .lines()
        .map(|line| line.unwrap())
        .collect();
    let mut n_words = 0;

    let start = std::time::Instant::now();
    for line in &lines {
        tokenizer.reset().push_str(line);
        tokenizer.do_tokenize().unwrap();
        morphemes.collect_results(&mut tokenizer).unwrap();
        n_words += morphemes.len();
    }
    let duration = start.elapsed();

    println!("Elapsed-{}: {} [sec]", series, duration.as_secs_f64());

    dbg!(n_words);

    // With BENCH_TOKENS=<file>, write the tokens of every line after the timed
    // loop, one per line with an empty line after each input line, for
    // segmentation.py. The timed loop above is unchanged.
    if let Ok(path) = std::env::var("BENCH_TOKENS") {
        let mut out = std::io::BufWriter::new(std::fs::File::create(path).unwrap());
        for line in &lines {
            tokenizer.reset().push_str(line);
            tokenizer.do_tokenize().unwrap();
            morphemes.collect_results(&mut tokenizer).unwrap();
            // Sudachi can give a morpheme an empty surface (inside "……", for
            // example); it covers no text, and an empty line would end the
            // line's tokens, so it is not written.
            for morpheme in morphemes.iter() {
                let surface = morpheme.surface();
                if !surface.is_empty() {
                    writeln!(out, "{}", &*surface).unwrap();
                }
            }
            writeln!(out).unwrap();
        }
    }
}
