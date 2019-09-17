clear variables; clear global; clear mex; close all; fclose('all'); clc
%%% NOTE: this code relies on functions from the PsychToolBox package,
%%% please make sure it is installed
%%% it furthermore uses I2MC, make sure you downloaded it and placed it in
%%% /function_library/I2MC

dbstop if error % for debugging: trigger a debug point when an error occurs

% setup directories
myDir = fileparts(mfilename('fullpath'));
cd(myDir);
cd data;                        dirs.data       = cd;
        cd samples_ophak;       dirs.samplesO   = cd;
cd ..;
if ~isdir('fixDet') %#ok<*ISDIR>
    mkdir(fullfile(cd,'fixDet'));
end
        cd fixDet;              dirs.fix        = cd;
cd ..;  cd msgs_ophak;          dirs.msgsO      = cd;
cd ..;
cd ..;  cd function_library;    dirs.funclib    = cd;
cd ..;  cd results;             dirs.out        = cd;
cd ..;
addpath(genpath(dirs.funclib));                 % add dirs to path

%%% params
% expt setup:
scrRes  = [1920 1080];
scrSz   = [34.95582 19.66265];      % in cm (these are for Spectrum with default screen)
freq    = 600;                      % Hz

% I2MC params:
disttoscreen = 65;  % cm, change to whatever is appropriate, though it matters little for I2MC
maxMergeDist = 15;
minFixDur    = 60;

%%% check I2MC (fixation classifier) is available
assert(~~exist('I2MCfunc','file'),'It appears that I2MC is not available. please follow the instructions in /readme_analysis_example/function_library/I2MC/get_I2MC.txt to download it.')

%%% get all trials, parse into subject and stimulus
[files,nfiles]  = FileFromFolder(dirs.samplesO,[],'txt');
files           = parseFileNames(files);

if 0
    % filter so we only get data that matches the filter. uses regexp
    filtstr = '^(?!01|02|03).*$';
    results = regexpi({files.name}.',filtstr,'start');
    files   = files(~cellfun(@isempty,results));
    nfiles  = length(files);
end

% create textfile and open for writing fixations
fid = fopen(fullfile(dirs.out,'allfixations.txt'),'w');
fprintf(fid,'File\tFixStart\tFixEnd\tFixDur\tXPos\tYPos\tRMSxy\tBCEA\tFixRangeX\tFixRangeY\n');

for p=1:nfiles
    fprintf('%s:\n',files(p).fname);
    % load data
    data    = readNumericFile(fullfile(dirs.samplesO,files(p).name),7,1);
    
    % load messges and trial mat file. We'll need to find when in trial the
    % stimulus came on to use that as t==0
    msgs    = loadMsgs(fullfile(dirs.msgsO,[files(p).fname '.txt']));
    [times,what,msgs] = parseMsgs(msgs);
    
    % event detection
    % make params struct (only have to specify those you want to be
    % different from their defaults)
    opt.xres          = scrRes(1);
    opt.yres          = scrRes(2);
    opt.missingx      = nan;
    opt.missingy      = nan;
    opt.scrSz         = scrSz;
    opt.disttoscreen  = disttoscreen;
    opt.freq          = freq;
    if opt.freq>120
        opt.downsamples   = [2 5 10];
        opt.chebyOrder    = 8;
    elseif opt.freq==120
        opt.downsamples   = [2 3 5];
        opt.chebyOrder    = 7;
    else
        % 90 Hz, 60 Hz, 30 Hz
        opt.downsampFilter= false;
        opt.downsamples   = [2 3];
    end
    if (~isfield(opt,'downsampFilter') || opt.downsampFilter) && ~exist('cheby1','file')
        warning('By default, I2MC runs a Chebyshev filter over the data as part of its operation. It appears that this filter (the function ''cheby1'' from the signal processing toolbox) is not available in your installation. I am thus disabling the filter.')
        opt.downsampFilter= false;
    end
    opt.maxMergeDist  = maxMergeDist;
    opt.minFixDur     = minFixDur;
    
    % make data struct
    clear dat;
    dat.time        = (data(:,1)-double(times.start))./1000; % mu_s to ms, make samples relative to onset of picture
    dat.left.X      = data(:,2);
    dat.left.Y      = data(:,3);
    dat.right.X     = data(:,4);
    dat.right.Y     = data(:,5);
    [fix,dat]       = I2MCfunc(dat,opt);
    
    % collect info and store
    dat.fix         = fix;
    dat.I2MCopt     = opt;
    save(fullfile(dirs.fix,[files(p).fname '.mat']),'dat');
    
    % also store to text file
    for f=1:numel(fix.start)
        fprintf(fid,'%s\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\n',files(p).fname, [fix.startT(f) fix.endT(f) fix.dur(f) fix.xpos(f) fix.ypos(f) fix.RMSxy(f), fix.BCEA(f), fix.fixRangeX(f), fix.fixRangeY(f)]);
    end
end

rmpath(genpath(dirs.funclib));                  % cleanup path
