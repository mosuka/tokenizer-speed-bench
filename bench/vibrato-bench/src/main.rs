use std::fs::File;
use std::io::BufRead;
use std::io::Write;

use clap::Parser;

use vibrato::{Dictionary, Tokenizer};

#[derive(Parser, Debug)]
#[clap(name = "main", about = "A program to benchmark.")]
struct Args {
    #[clap(long)]
    dictname: String,
}

fn main() {
    let args = Args::parse();

    let rootdir = env!("CARGO_MANIFEST_DIR");
    let dictname = args.dictname;

    let reader =
        zstd::Decoder::new(File::open(format!("{rootdir}/{dictname}/system.dic.zst")).unwrap())
            .unwrap();
    let dict = Dictionary::read(reader).unwrap();
    let tokenizer = Tokenizer::new(dict);
    let mut worker = tokenizer.new_worker();

    let lines: Vec<_> = std::io::stdin()
        .lock()
        .lines()
        .map(|line| line.unwrap())
        .collect();
    let mut n_words = 0;

    let start = std::time::Instant::now();
    for line in &lines {
        worker.reset_sentence(line);
        worker.tokenize();
        n_words += worker.num_tokens();
    }
    let duration = start.elapsed();

    println!(
        "Elapsed-vibrato-{}: {} [sec]",
        dictname,
        duration.as_secs_f64()
    );

    dbg!(n_words);

    // With BENCH_TOKENS=<file>, write the tokens of every line after the timed
    // loop, one per line with an empty line after each input line, for
    // segmentation.py. The timed loop above is unchanged.
    if let Ok(path) = std::env::var("BENCH_TOKENS") {
        let mut out = std::io::BufWriter::new(std::fs::File::create(path).unwrap());
        for line in &lines {
            worker.reset_sentence(line);
            worker.tokenize();
            for i in 0..worker.num_tokens() {
                writeln!(out, "{}", worker.token(i).surface()).unwrap();
            }
            writeln!(out).unwrap();
        }
    }
}
