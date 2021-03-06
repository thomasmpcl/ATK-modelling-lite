/**
 * \file StaticModelFilter.h
 */

#ifdef ENABLE_CLANG_SUPPORT

#ifdef __APPLE__
#include <boost/filesystem.hpp>
namespace fs=boost::filesystem;
#else
#include <filesystem>
namespace fs=std::filesystem;
#endif
#include <fstream>
#include <sstream>

#include <clang/AST/ASTContext.h>
#include <clang/AST/ASTConsumer.h>
#include <clang/Basic/DiagnosticOptions.h>
#include <clang/Basic/Diagnostic.h>
#include <clang/Basic/FileManager.h>
#include <clang/Basic/FileSystemOptions.h>
#include <clang/Basic/LangOptions.h>
#include <clang/Basic/MemoryBufferCache.h>
#include <clang/Basic/SourceManager.h>
#include <clang/Basic/TargetInfo.h>
#include <clang/CodeGen/CodeGenAction.h>
#include <clang/Frontend/CompilerInstance.h>
#include <clang/Frontend/CompilerInvocation.h>
#include <clang/Frontend/TextDiagnosticPrinter.h>
#include <clang/Lex/HeaderSearch.h>
#include <clang/Lex/HeaderSearchOptions.h>
#include <clang/Lex/Preprocessor.h>
#include <clang/Lex/PreprocessorOptions.h>
#include <clang/Parse/ParseAST.h>
#include <clang/Sema/Sema.h>

#include <llvm/InitializePasses.h>
#include <llvm/ExecutionEngine/ExecutionEngine.h>
#include <llvm/ExecutionEngine/MCJIT.h>
#include <llvm/ExecutionEngine/SectionMemoryManager.h>
#include <llvm/IR/DataLayout.h>
#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/PassManager.h>
#include <llvm/Passes/PassBuilder.h>
#include <llvm/Support/MemoryBuffer.h>
#include <llvm/Support/TargetSelect.h>
#include <llvm/Support/raw_ostream.h>

#include <ATK/Core/BaseFilter.h>
#include <ATK/Core/Utilities.h>

#include "StaticModelFilter.h"

namespace
{
  class GlobalHandler
  {
  public:
    ~GlobalHandler()
    {
      executionEngine.reset();
    }

    llvm::LLVMContext context;
    std::unique_ptr<llvm::ExecutionEngine> executionEngine;
  };

  GlobalHandler handler;

  bool LLVMinit = false;
  
  void InitializeLLVM()
  {
    if (LLVMinit)
    {
      return;
    }
    // We have not initialized any pass managers for any device yet.
    // Run the global LLVM pass initialization functions.
    llvm::InitializeNativeTarget();
    llvm::InitializeNativeTargetAsmPrinter();
    llvm::InitializeNativeTargetAsmParser();

    auto& Registry = *llvm::PassRegistry::getPassRegistry();
    
    llvm::initializeCore(Registry);
    llvm::initializeScalarOpts(Registry);
    llvm::initializeVectorization(Registry);
    llvm::initializeIPO(Registry);
    llvm::initializeAnalysis(Registry);
    llvm::initializeIPO(Registry);
    llvm::initializeTransformUtils(Registry);
    llvm::initializeInstCombine(Registry);
    llvm::initializeInstrumentation(Registry);
    llvm::initializeTarget(Registry);
    
    LLVMinit = true;
  }
}

namespace ATK
{
  template<typename DataType>
  StaticModelFilterGenerator<DataType>::~StaticModelFilterGenerator()
  {
  }
  
  template<typename DataType>
  std::unique_ptr<BaseFilter> StaticModelFilterGenerator<DataType>::generateDynamicFilter() const
  {
    return std::unique_ptr<BaseFilter>();
  }

  template<typename Function>
  Function parseString(const std::string& fullfile, const std::string& function)
  {
    auto temp_dir = fs::temp_directory_path();

    auto filename = temp_dir / "SPICE.cpp";

    {
      std::ofstream file(filename.string());

      file << fullfile << std::endl;
    }

    Function fun = parseFile<Function>(filename.string(), function);
    fs::remove(filename);

    return fun;
  }

  template<typename Function>
  Function parseFile(const std::string& filename, const std::string& function)
  {
    InitializeLLVM();
    
    clang::DiagnosticOptions diagnosticOptions;
    std::unique_ptr<clang::TextDiagnosticPrinter> textDiagnosticPrinter =
      std::make_unique<clang::TextDiagnosticPrinter>(llvm::outs(),
                                                     &diagnosticOptions);
    llvm::IntrusiveRefCntPtr<clang::DiagnosticIDs> diagIDs;
    
    std::unique_ptr<clang::DiagnosticsEngine> diagnosticsEngine =
      std::make_unique<clang::DiagnosticsEngine>(diagIDs, &diagnosticOptions, textDiagnosticPrinter.get());
    
    clang::CompilerInstance compilerInstance;
    auto& compilerInvocation = compilerInstance.getInvocation();
    
    std::stringstream ss;
    ss << "-triple=" << llvm::sys::getDefaultTargetTriple();

    std::istream_iterator<std::string> begin(ss);
    std::istream_iterator<std::string> end;
    std::istream_iterator<std::string> i = begin;
    std::vector<const char*> itemcstrs;
    std::vector<std::string> itemstrs;
    while (i != end) {
      itemstrs.push_back(*i);
      ++i;
    }
    
    for (unsigned idx = 0; idx < itemstrs.size(); idx++) {
      // note: if itemstrs is modified after this, itemcstrs will be full
      // of invalid pointers! Could make copies, but would have to clean up then...
      itemcstrs.push_back(itemstrs[idx].c_str());
    }

    clang::CompilerInvocation::CreateFromArgs(compilerInvocation, itemcstrs.data(), itemcstrs.data() + itemcstrs.size(),
     *diagnosticsEngine.release());

    auto* languageOptions = compilerInvocation.getLangOpts();
    auto& preprocessorOptions = compilerInvocation.getPreprocessorOpts();
    auto& targetOptions = compilerInvocation.getTargetOpts();
    auto& frontEndOptions = compilerInvocation.getFrontendOpts();
#ifdef DEBUG
    frontEndOptions.ShowStats = true;
#endif
    auto& headerSearchOptions = compilerInvocation.getHeaderSearchOpts();
#ifdef DEBUG
    headerSearchOptions.Verbose = true;
#endif
    auto& codeGenOptions = compilerInvocation.getCodeGenOpts();

    frontEndOptions.Inputs.clear();
    frontEndOptions.Inputs.push_back(clang::FrontendInputFile(filename, clang::InputKind::CXX));
    
    targetOptions.Triple = llvm::sys::getDefaultTargetTriple();
    compilerInstance.createDiagnostics(textDiagnosticPrinter.get(), false);

    std::unique_ptr<clang::CodeGenAction> action = std::make_unique<clang::EmitLLVMOnlyAction>(&handler.context);
    
    if (!compilerInstance.ExecuteAction(*action))
    {
      throw ATK::RuntimeError("Failed to compile file");
    }

    std::unique_ptr<llvm::Module> module = action->takeModule();
    if (!module)
    {
      throw ATK::RuntimeError("Failed to retrieve module");
    }

    llvm::PassBuilder passBuilder;
    llvm::LoopAnalysisManager loopAnalysisManager(codeGenOptions.DebugPassManager);
    llvm::FunctionAnalysisManager functionAnalysisManager(codeGenOptions.DebugPassManager);
    llvm::CGSCCAnalysisManager cGSCCAnalysisManager(codeGenOptions.DebugPassManager);
    llvm::ModuleAnalysisManager moduleAnalysisManager(codeGenOptions.DebugPassManager);

    passBuilder.registerModuleAnalyses(moduleAnalysisManager);
    passBuilder.registerCGSCCAnalyses(cGSCCAnalysisManager);
    passBuilder.registerFunctionAnalyses(functionAnalysisManager);
    passBuilder.registerLoopAnalyses(loopAnalysisManager);
    passBuilder.crossRegisterProxies(loopAnalysisManager, functionAnalysisManager, cGSCCAnalysisManager, moduleAnalysisManager);

    llvm::ModulePassManager modulePassManager = passBuilder.buildPerModuleDefaultPipeline(llvm::PassBuilder::OptimizationLevel::O3);
    modulePassManager.run(*module, moduleAnalysisManager);
    
    llvm::EngineBuilder builder(std::move(module));
    builder.setMCJITMemoryManager(std::make_unique<llvm::SectionMemoryManager>());
    builder.setOptLevel(llvm::CodeGenOpt::Level::Aggressive);
    handler.executionEngine.reset(builder.create());
    
    if (!handler.executionEngine)
    {
      throw ATK::RuntimeError("Failed to compile file when retrieving the module");
    }

    return reinterpret_cast<Function>(handler.executionEngine->getFunctionAddress(function));
  }
  
  typedef int(*IntInt)(int);
  template ATK_MODELLING_EXPORT IntInt parseString<IntInt>(const std::string& fullfile, const std::string& function);
  typedef int(*IntInt)(int);
  template ATK_MODELLING_EXPORT IntInt parseFile<IntInt>(const std::string& filenqme, const std::string& function);
}

#endif

