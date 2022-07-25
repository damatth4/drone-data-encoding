sample_rate = 192000;
period = 1/sample_rate;

 
figure(1)
pspectrum(bitTest, sample_rate, 'spectrogram', 'FrequencyLimits',[0 70000], 'TimeResolution',.01);
title({'bit test sampled at 192kHz';  'Fres = 375.3666 Hz, Tres = 10 ms'})

%%
[p, f, time] = pspectrum(bitTest, sample_rate, 'spectrogram', 'FrequencyLimits',[0 70000], 'TimeResolution', .01);

%%

% time of bitTest
bitTestTime = length(bitTest')/192e3;

% bins per one second
binsPerSecond = length(time')/bitTestTime;

%%

% "clc" clears the cmd, "close all" closes the figures
clc; close all;

% iterate through spectrogram matrix
DURATION_OF_HI = 0.01; % seconds
FREQ_LO = 580; % bottom range
FREQ_HI = 730; % upper range

% total bins on x axis
t = length(time');

% bins per DURATION_OF_HI
b = round(binsPerSecond * DURATION_OF_HI);

resultAvgs = zeros([1, round(t/b)]);

idx = 1; % index in resultAvgs
while idx <= t/b
    % find the mean value of the sub matrix
    sum = 0.0;
    total = 0.0;
    for r = FREQ_LO:FREQ_HI
        for c = 1:b
            sum = sum + p(r, c + ((idx - 1) * b));
            total = total + 1;
        end
    end
    
    % add this avg to our result
    avg = sum/total;
    resultAvgs(1, idx) = avg;
    
    % incrememnt index for result lisst
    idx = idx + 1;
end

% display
% resultAvgs

%%

plot(1:length(resultAvgs), resultAvgs)

%% decode data and get bits

totalTimeBins = length(resultAvgs);
HI_BAR = 0.5e-7; % passing above means 1
LO_BAR = 4e-9; % passing below means 0

result = [];

bin = 1;
prevVal = 0.0;
while bin <= totalTimeBins
    val = resultAvgs(1, bin);
    % if we have passed the threshhold, append 1 to result
    if (val > HI_BAR && prevVal <= HI_BAR)
        result = [result 1];
    elseif (val < LO_BAR && prevVal >= LO_BAR)
        result = [result 0];
    end
    prevVal = val;
    bin = bin + 1;
end

result

%% clean up (bc signal has partial manchester encoding)

finalResult = [];

bit = 1;
len = length(result);

while bit <= len
    val = result(bit);
    if (val == 1)
        bit = bit + 1;
        % '10' = 1 so skip over consecutive 1s
        while (bit <= len) && (result(bit) ~= 0)
            bit = bit + 1;
        end
        finalResult = [finalResult 1];
    else % val == 0
        finalResult = [finalResult 0];
    end
    bit = bit + 1;
end

finalResult



