package lucene_nori_bench;

import java.io.IOException;
import java.io.StringReader;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;
import org.apache.lucene.analysis.TokenStream;
import org.apache.lucene.analysis.ko.KoreanTokenizer;

public class App {
    public static void main(String[] args) throws IOException {
        // DecompoundMode.NONE emits dictionary entries whole, like the alyze
        // and lindera ko-dic rows; Lucene's default is DecompoundMode.DISCARD.
        // No unigrams for unknown words, and punctuation is discarded, which
        // are the defaults.
        KoreanTokenizer tokenizer = new KoreanTokenizer(TokenStream.DEFAULT_TOKEN_ATTRIBUTE_FACTORY, null,
                KoreanTokenizer.DecompoundMode.NONE, false, true);
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
        System.out.println("Elapsed-lucene-nori: " + timeElapsed + " [sec]");
        System.out.println(n_words);
    }
}
