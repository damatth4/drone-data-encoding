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
DURATION_OF_HI = 0.03; % seconds
FREQ_LO = 600; % bottom range - around 40 kHz (587th freq bin based on f)
FREQ_HI = 730; % upper range - around 50 kHz

% total bins on x axis
t = length(time');

% bins per DURATION_OF_HI
b = round(binsPerSecond * DURATION_OF_HI);

resultAvgs = zeros([1, round(t/b)]);

idx = 1; % index in resultAvgs
while idx < t/b
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
resultAvgs

%%

plot(1:131, resultAvgs)

