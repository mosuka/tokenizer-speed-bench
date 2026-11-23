package lucene_kuromoji_bench;

import java.io.IOException;
import java.io.StringReader;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;
import org.apache.lucene.analysis.ja.JapaneseTokenizer;

public class App {
    public static void main(String[] args) throws IOException {
        // Normal mode does not decompound, like the alyze, lindera, mecab and
        // vibrato rows; Lucene's default is Mode.SEARCH. Punctuation is
        // discarded, as in the alyze rows.
        JapaneseTokenizer tokenizer = new JapaneseTokenizer(null, true, JapaneseTokenizer.Mode.NORMAL);
        Scanner input = new Scanner(System.in, "utf-8");
        List<String> lines = new ArrayList<String>();
        while (input.hasNext()) {
            lines.add(input.nextLine());
        }
        Instant start = Instant.now();
        int n_words = 0;
        for (String line : lines) {
            // One tokenizer is reused for every line, as Lucene intends.
            tokenizer.setReader(new StringReader(line));
            tokenizer.reset();
            while (tokenizer.incrementToken()) {
                n_words++;
            }
            tokenizer.end();
            tokenizer.close();
        }
        Instant finish = Instant.now();
        double timeElapsed = (double) Duration.between(start, finish).toNanos() / 1000000000;
        System.out.println("Elapsed-lucene-kuromoji: " + timeElapsed + " [sec]");
        System.out.println(n_words);
    }
}
