%% inputs from user
clc;
close all;
clear;

inp = input('Input the bin duration. Recommended bin duration is 1/2 of the bit length. Input must be a number: ');
BIN_LENGTH = inp; 

matrixName = input('Input the sound file you want to process: ', 's');
[data,fs] = audioread(matrixName);
sample_rate = fs;
soundMatrix = data;
%%
period = 1/sample_rate;

% creates blue and yellow graph to see frequency and power over time
% figure(1)
% pspectrum(soundMatrix, sample_rate, 'spectrogram', 'FrequencyLimits',[1000 30000], 'TimeResolution',.01);

%%
[p, f, time] = pspectrum(soundMatrix, sample_rate, 'spectrogram', 'FrequencyLimits',[1000 30000], 'TimeResolution', .01);
% gets three variables from spectrogram
%%
% getting some calculations???? hmmmm...
% 
%  PREFORMATTED
%  TEXT
% 
% time of bitTest
bitTestTime = length(soundMatrix')/192e3;

% bins per one second
binsPerSecond = length(time')/bitTestTime;

%%

% "clc" clears the cmd, "close all" closes the figures
% clc; close all;

% iterate through spectrogram matrix
% HALF_BIT_DURATION = 0.25; % seconds

% frequency ranges for high and low
% y-axis of spectrogram defines frequencies
% NOTE: LO_RANGE does NOT corrrespond to "lowF" in the python code. same
% with HIGH_RANGE and "highF". they are inverted here
LO_RANGE = [340, 365]; % 10.6 - 11.3
HI_RANGE = [584, 636]; % 17.5 - 19
BASE_RANGE = [449, 485]; % 13.7 - 14.7
SIGNAL_THRESHOLD = -64;

% power threshold for high and low
% LO_POWER = -57;
% HI_POWER = -70;
% colors in spectrogram threshold for seeing bit

% total bins on x axis
t = length(time');

% bins per HALF_BIT_DURATION
b = round(binsPerSecond * BIN_LENGTH);

avgLoRes = zeros([1, round(t/b)]);
avgHiRes = zeros([1, round(t/b)]);

idx = 1; % index in resultAvgs
% t is ___ and b is ________
% iterating through every pixel in a range (aka the sub matrix)
while idx <= t/b
    % find the mean value of the low range sub matrix
    sumLo = 0.0;
    totalLo = 0.0;
    % 2D loop for 2D matrix (2D pixel box)
    for r = LO_RANGE(1):LO_RANGE(2)
        for c = 1:b
            sumLo = sumLo + p(r, c + ((idx - 1) * b));
            totalLo = totalLo + 1;
        end
    end
    avgLo = sumLo/totalLo;
    avgLoRes(1, idx) = avgLo;
    
     % find the mean value of the high range sub matrix
    sumHi = 0.0;
    totalHi = 0.0;
    for r = HI_RANGE(1):HI_RANGE(2)
        for c = 1:b
            % accessing every individual cell
            sumHi = sumHi + p(r, c + ((idx - 1) * b));
            totalHi = totalHi + 1;
        end
    end
    avgHi = sumHi/totalHi;
    avgHiRes(1, idx) = avgHi;
    idx = idx + 1;
end

%% trim out unecessary parts of the matrix
idx = 1;
startIdx = 1;
while idx <= length(avgHiRes)%% we check hi because we start every message with four 1's (hi lo base)
    if pow2db(avgHiRes(idx)) >= SIGNAL_THRESHOLD
        startIdx = idx;
        break;
    end
    idx = idx + 1;
end

idx = length(avgLoRes);
endIdx = length(avgLoRes);
while idx >= 1 %% we check lo because we end every message with four 0's (lo hi base)
    if pow2db(avgLoRes(idx)) >= SIGNAL_THRESHOLD
        endIdx = idx;
        break;
    end
    idx = idx - 1;
end

avgLoRes = avgLoRes(startIdx:endIdx);
avgHiRes = avgHiRes(startIdx:endIdx);
result = zeros([1, length(avgLoRes)]);

%% translate into pre-machester-decoding
% set power thresholds    
LO_POWER = pow2db(mean(avgLoRes)); % this method works better than taking the middle of the min and max
HI_POWER = pow2db(mean(avgHiRes));

% iterate through 
idx = 1;
while idx <= length(result)
    
    avgLo = avgLoRes(idx);
    avgHi = avgHiRes(idx);

    % check if avgLo passes power threshold
    if pow2db(avgLo) > LO_POWER
        result(1, idx) = -1;
    elseif pow2db(avgHi) > HI_POWER
        result(1,idx) = 1;
    else
        result(1, idx) = 0;
    end
    
    % incrememnt index for result list
    idx = idx + 1;
end
% end result is a 1D matrix for low and 1D matrix for high

%% clean up, manchester decoding

finalResult = [];

bit = 1;
len = length(result);
% 1 is 1, -1 is 0, 0 is lack of signal
while bit <= len
    val = result(bit);
    if (val == 1)
        bit = bit + 1;
        % '1 -1' = 1 so skip over consecutive 1s
        while (bit <= len) && (result(bit) == 1)
            bit = bit + 1;
        end
        % ensure we went from 1 to -1
        if ((bit <= len) && (result(bit) == -1)) 
            while (bit <= len) && (result(bit) == -1)
                bit = bit + 1;
            end
            finalResult = [finalResult 1];
        end  
        
    elseif (val == -1)
        bit = bit + 1;
        % '-1 1' = 0 so skip over consecutive -1s
        while (bit <= len) && (result(bit) == -1)
            bit = bit + 1;
        end
        % ensure we go from -1 to 1
        if ((bit <= len) && (result(bit) == 1))
            while (bit <= len) && (result(bit) == 1)
                bit = bit + 1;
            end
            finalResult = [finalResult 0];
        end
        
    else
        bit = bit + 1;
    end
    
end

%% look for header and footer
startIdx = 1;
endIdx = length(finalResult);
onesInARow = 0;
zerosInARow = 0;
while startIdx <= length(finalResult)
    if finalResult(startIdx) == 1
        onesInARow = onesInARow + 1;
    else
        onesInARow = 0;
    end
    if onesInARow == 4
        startIdx = startIdx + 1;
        break
    end
    startIdx = startIdx + 1;
end

while endIdx >= 1
    if finalResult(endIdx) == 0
        zerosInARow = zerosInARow + 1;
    else
        zerosInARow = 0;
    end
    if zerosInARow == 4
        endIdx = endIdx - 1;
        break
    end
    endIdx = endIdx - 1;
end
validString = false;
if startIdx < endIdx
    validString = true;
end

%% display result
disp(append(newline, 'data: ', num2str(finalResult)));
disp(append('length: ', string(length(finalResult))));
% disp(append('number of bits: ', string(length(finalResult)), ' total bits - ', '8 extraneous bits', ' = ', string(length(finalResult) - 8), ' actual bits'));

if validString
    % chop off first four digits and last four digits
    finalResult = finalResult(startIdx:endIdx);
    disp(append('translating: ', num2str(finalResult)));
    disp(append('length: ', string(length(finalResult))));

    if mod(length(finalResult), 8) == 0
        letterMatrix = char(bin2dec(reshape(char('0' + finalResult),8,[]).'));
        letterMatrix = letterMatrix';
        finalString = string(letterMatrix);
        disp(append(newline, 'translated string: ', finalString));
    else
        disp("the sound data cannot be translated :(");
    end
else
    disp('message is missing header or footer');
end
