set terminal dumb 80 40
set title 'Average Rate Over Time'
set xlabel 'Sample Number'
set ylabel 'Average Rate'
set grid

# Style the plot
set style line 1 lc rgb '#0060ad' lt 1 lw 2 pt 7 ps 1.5

# Get input file from command line argument
inputfile = ARG1

plot inputfile using 1:2 with linespoints ls 1 title 'Average Rate' 