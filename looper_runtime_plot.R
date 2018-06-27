#! /usr/bin/env Rscript
###############################################################################
#06/04/18
#Last Updated 06/27/18
#Original Author: Jason Smith
#looper_runtime_plot.R
#
#This program is meant to plot a comparison of total runtime to a breakdown
#of the runtime for each pipeline subcommand
#
#NOTES:
#usage: Rscript /path/to/Rscript/looper_runtime_plot.R 
#       /path/to/project_config.yaml
#
#requirements: argparser, dplyr, ggplot2, grid, stringr, pepr
#
###############################################################################
####                              DEPENDENCIES                             ####
###############################################################################
##### LOAD ARGUMENTPARSER #####
loadLibrary <- tryCatch (
    {
        suppressWarnings(suppressPackageStartupMessages(library(argparser)))
    },
    error=function(e) {
        message("Error: Install the \"argparser\"",
                " library before proceeding.")
        return(NULL)
    },
    warning=function(e) {
        message(e)
        return(TRUE)
    }
)
if (length(loadLibrary)!=0) {
    suppressWarnings(library(argparser))
} else {
    quit()
}

# Create a parser
p <- arg_parser("Produce an ATACseq pipeline (PEPATAC) runtime plot")

# Add command line arguments
p <- add_argument(p, "config", 
                  help="PEPATAC project_config.yaml")
# p <- add_argument(p, "--output", 
                  # help="PNG or PDF",
                  # default = "PDF")

# Parse the command line arguments
argv <- parse_args(p)

##### LOAD ADDITIONAL DEPENDENCIES #####
required_libraries <- c("dplyr", "ggplot2", "grid", "stringr", "pepr")
for (i in required_libraries) {
    loadLibrary <- tryCatch (
        {
            suppressPackageStartupMessages(
                suppressWarnings(library(i, character.only=TRUE)))
        },
        error=function(e) {
            message("Error: Install the \"", i,
                    "\" library before proceeding.")
            return(NULL)
        },
        warning=function(e) {
            message(e)
            return(1)
        }
    )
    if (length(loadLibrary)!=0) {
        suppressWarnings(library(i, character.only=TRUE))
    } else {
        quit()
    }
}

###############################################################################
####                               FUNCTIONS                               ####
###############################################################################
# Convert Hours:Minutes:Seconds to Seconds 
toSeconds <- function(HMS){
    if (!is.character(HMS)) {
        stop("HMS must be a character string of the form H:M:S")
    }
    if (length(HMS)<=0){
        return(HMS)
    }
    unlist(
        lapply(HMS,
               function(i){
                   i <- as.numeric(strsplit(i,':',fixed=TRUE)[[1]])
                   if      (length(i) == 3) {i[1]*3600 + i[2]*60 + i[3]}
                   else if (length(i) == 2) {i[1]*60 + i[2]}
                   else if (length(i) == 1) {i[1]}
               }))
} 

# Convert seconds back to HMS format
secondsToString <- function(secs, digits=2){
    unlist(
        lapply(secs,
               function(i){
                   # includes fractional seconds
                   fs  <- as.integer(round((i - round(i))*(10^digits)))
                   fmt <- ''
                   if (i >= 3600)    {fmt <- '%H:%M:%S'}
                   else if (i >= 60) {fmt <- '%M:%S'}
                   else              {fmt <- '%OS'}
                   i   <- format(as.POSIXct(strptime("0:0:0","%H:%M:%S")) +
                                 i, format=fmt)
                   if (fs > 0) {sub('[0]+$','',paste(i,fs,sep='.'))}
                   else        {i}
               }))
}

# Taken from https://github.com/baptiste/egg/blob/master/R/set_panel_size.r
set_panel_size <- function(p=NULL, g=ggplotGrob(p), file=NULL, 
                           margin=unit(1, "in"),
                           width=unit(4, "in"), 
                           height=unit(4, "in")){
    
    panels <- grep("panel", g$layout$name)
    panel_index_w <- unique(g$layout$l[panels])
    panel_index_h <- unique(g$layout$t[panels])
    nw <- length(panel_index_w)
    nh <- length(panel_index_h)
    
    if(getRversion() < "3.3.0"){
        
        # the following conversion is necessary
        # because there is no `[<-`.unit method
        # so promoting to unit.list allows standard list indexing
        g$widths  <- grid:::unit.list(g$widths)
        g$heights <- grid:::unit.list(g$heights)
        
        g$widths[panel_index_w]  <- rep(list(width), nw)
        g$heights[panel_index_h] <- rep(list(height), nh)
        
    } else {
        
        g$widths[panel_index_w]  <- rep(width, nw)
        g$heights[panel_index_h] <- rep(height, nh)
        
    }
    
    if(!is.null(file))
        ggsave(file, g, limitsize = FALSE,
               width=convertWidth(sum(g$widths) + margin, 
                                  unitTo="in", valueOnly=TRUE),
               height=convertHeight(sum(g$heights) + margin,  
                                    unitTo="in", valueOnly=TRUE))
    
    invisible(g)
}

# Helper function to build a file path to the correct output folder using a
# specified suffix
buildFilePath = function(sampleName, suffix, pep=prj) {
    invisible(capture.output(outputDir <- config(pep)$metadata$output_dir))
    file.path(outputDir, "results_pipeline", sampleName,
              paste(sampleName, suffix, sep=""))
}

# Remove sequentially duplicated values in a column, summing the values
# in the other
dedupSequential = function(dupDF) {
    dupList <- dupDF[c(tail(dupDF[,1],-1) != head(dupDF[,1],-1), TRUE),][,1]
    dedupDF <- data.frame(cmd=character(length(dupList)),
                          val=numeric(length(dupList)),
                          stringsAsFactors=FALSE)
    currentPos <- 1
    counter    <- 1
    while (counter <= nrow(dupDF)) {
        currentCmd <- dupDF[counter, 1]
        total      <- dupDF[counter, 2]
        if (counter + 1 < nrow(dupDF)) {
            nextCmd     <- dupDF[counter + 1, 1]
            while (nextCmd == currentCmd) {
                counter <- counter + 1
                total   <- total + dupDF[counter, 2]
                nextCmd <- dupDF[counter + 1, 1]
            }
        }
        dedupDF[currentPos, 1] <- currentCmd
        dedupDF[currentPos, 2] <- total
        currentPos <- currentPos + 1
        counter    <- counter + 1
    }
    return (dedupDF)
}

# Produce a runtime plot for a sample
getRuntime = function(timeFile, sampleName) {
    # Get just the first line to get pipeline start time
    startTime  <- readLines(timeFile, n=1)

    # Extract just the starting time timestamp
    startTime  <- word(startTime, -1, sep=" ")

    # Get the run times for each pipeline command
    # Ignore any lines containing '#'
    timeStamps <- read.delim2(timeFile, skip=2, header = FALSE,
                              as.is=TRUE, comment.char = '#')

    # Remove leading directory structure
    for (i in 1:nrow(timeStamps)) {
        timeStamps[i,1]  <- sub('.*\\/', '', timeStamps[i,1])   
    }
    timeStamps           <- timeStamps[,-c(2,4)]
    colnames(timeStamps) <- c("cmd","time")

    timeStamps$time <- toSeconds(timeStamps$time)
    
    # Combine any of the same commands to get total time spent per command
    # Eliminate only sequentially duplicated commands
    combinedTime <- dedupSequential(timeStamps)
    colnames(combinedTime) <- c("cmd", "time")
    
    totalTime       <- sum(combinedTime$time)
    finishTime      <- secondsToString(toSeconds(startTime) + totalTime)

    num.rows <- nrow(combinedTime)
    combinedTime[num.rows+1, 1] <- "totalTime"
    combinedTime[num.rows+1, 2] <- as.character(totalTime)

    combinedTime$time  <- as.numeric(combinedTime$time)
    combinedTime$cmd   <- as.character(combinedTime$cmd)
    # Set order for plotting purposes
    combinedTime$order <- as.factor(as.numeric(row.names(combinedTime)))
    
    # Create plot
    p <- ggplot(data=combinedTime, aes(x=order, y=time)) +
                geom_bar(stat="identity", position=position_dodge())+
                scale_fill_brewer(palette="Paired")+
                theme_minimal() +
                coord_flip() +
                labs(y = paste("Time (s)\n", "[Start: ", startTime, " | ", 
                               "End: ", finishTime, "]", sep=""),
                     x = "PEPATAC Command") +
                scale_x_discrete(labels=combinedTime$cmd) +
                theme(plot.title = element_text(hjust = 0.5))
    
    # Produce both PDF and PNG
    set_panel_size(
        p, 
        file=buildFilePath(sampleName, "_Runtime.pdf", prj), 
        width=unit(8,"inches"), 
        height=unit(5.5,"inches"))
    set_panel_size(
        p, 
        file=buildFilePath(sampleName, "_Runtime.png", prj), 
        width=unit(8,"inches"), 
        height=unit(5.5,"inches"))
    
    return(combinedTime)
}

###############################################################################
####                               OPEN FILE                               ####
###############################################################################

configFile <- argv$config
prj = Project(configFile)

###############################################################################
####                                 MAIN                                  ####
###############################################################################
# For each sample in the project, produce a runtime summary plot
if (!is.null(config(prj)$name)) {
    accumName <- file.path(config(prj)$metadata$output_dir,
                           paste(config(prj)$name, "average_runtime.csv",
                                 sep="_"))
} else {
    accumName <- file.path(config(prj)$metadata$output_dir,
                           "average_runtime.csv")
}
invisible(capture.output(outputDir <- config(prj)$metadata$output_dir))
invisible(capture.output(numSamples <- length(samples(prj)$sample_name)))
accumulated <- data.frame(cmd=as.character(), time=as.numeric(), order=as.numeric())
for (i in 1:numSamples) {
    invisible(capture.output(sampleName <- samples(prj)$sample_name[i]))
    timeFile <- Sys.glob(file.path(outputDir, "results_pipeline",
                                   sampleName, "*_profile.tsv"))
    combinedTime <- getRuntime(timeFile, sampleName)
    if (i == 1) {
        accumulated <- combinedTime
    } else {
        accumulated <- full_join(accumulated, combinedTime, by=c("cmd","order"))
    }
}
accumulated <- accumulated[,-c(2,3)]
final <- data.frame(cmd=as.character(), average_time=as.numeric())
for (i in 1:nrow(accumulated)) {
    cmd <- accumulated$cmd[i]
    tmp <- accumulated[,-1]
    average_time <- as.numeric(sum(tmp[i,], na.rm=TRUE))/(ncol(tmp)-1)
    average = data.frame(cbind(cmd, average_time))
    final <- rbind(final, average)
}
write.csv(final, accumName, row.names=FALSE)

write("Completed!\n", stdout())