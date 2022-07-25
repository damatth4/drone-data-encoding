sample_rate = 192000;
period = 1/sample_rate;

% creates blue and yellow graph to see frequency and power over time
figure(1)
pspectrum(boeing, sample_rate, 'spectrogram', 'FrequencyLimits',[1000 30000], 'TimeResolution',.01);
title({'bit test sampled at 192kHz';  'Fres = 375.3666 Hz, Tres = 10 ms'})

%%
[p, f, time] = pspectrum(boeing, sample_rate, 'spectrogram', 'FrequencyLimits',[1000 30000], 'TimeResolution', .01);
% gets three variables from spectrogram
%%
% getting some calculations???? hmmmm...
% time of bitTest
bitTestTime = length(boeing')/192e3;

% bins per one second
binsPerSecond = length(time')/bitTestTime;

%%

% "clc" clears the cmd, "close all" closes the figures
clc; close all;

% iterate through spectrogram matrix
HALF_BIT_DURATION = 0.25; % seconds

% frequency ranges for high and low
% y-axis of spectrogram defines frequencies
LO_RANGE = [330, 378]; % [10.3e3, 11.7e3]
HI_RANGE = [583, 643]; % [17.5e3, 19.2e3]

% power threshold for high and low
LO_POWER = -77;
HI_POWER = -78;
% colors in spectrogram threshold for seeing bit

% total bins on x axis
t = length(time');

% bins per HALF_BIT_DURATION
b = round(binsPerSecond * HALF_BIT_DURATION);

result = zeros([1, round(t/b)]);

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
    
    % check if avgLo is passes power threshold
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
% display
% result
% plot(1:length(result), result)

%%
plot(1:length(avgLoRes), avgLoRes);

%%
plot(1:length(avgHiRes), avgHiRes);


%% clean up (bc signal has partial manchester encoding)

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

% remove the first 1 and drop last 4 0's -> Hello Boeing
finalResult
% corresponds to 1s and 0s that correspond to hello boeing
%%
plot(f(583:643),pow2db(p((583:643),:)))

%%
plot(0:length(boeing)-1,boeing)

