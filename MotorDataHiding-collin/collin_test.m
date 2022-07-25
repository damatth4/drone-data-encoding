% figure(1)
% plot(avgLoRes)
% title('avgLoRes')
% xlabel('samples')
% ylabel('frequency')
% figure(2)
% plot(avgHiRes)
% title('avgHiRes')
% xlabel('samples')
% ylabel('frequency')
x = data;
y = fft(x);
n = length(x);          % number of samples
f = (0:n-1)*(fs/n);     % frequency range
power = abs(y).^2/n;    % power of the DFT

plot(f,power)
xlabel('Frequency')
ylabel('Power')